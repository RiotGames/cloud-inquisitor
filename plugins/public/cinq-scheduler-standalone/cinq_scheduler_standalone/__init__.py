from datetime import datetime, timedelta

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler as APScheduler
from cloud_inquisitor import app_config, AWS_REGIONS
from cloud_inquisitor.config import ConfigOption
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import CollectorType, BaseScheduler
from cloud_inquisitor.plugins.types.accounts import BaseAccount, AWSAccount
from cloud_inquisitor.schema import LogEvent


class StandaloneScheduler(BaseScheduler):
    """Main workers refreshing data from AWS
    """
    name = 'Standalone Scheduler'
    ns = 'scheduler_standalone'
    pool = None
    scheduler = None
    options = (
        ConfigOption('worker_threads', 20, 'int', 'Number of worker threads to spawn'),
        ConfigOption('worker_interval', 30, 'int', 'Delay between each worker thread being spawned, in seconds'),
    )

    def __init__(self):
        super().__init__()
        self.collectors = {}
        self.auditors = []
        self.region_workers = []

        self.pool = ProcessPoolExecutor(self.dbconfig.get('worker_threads', self.ns, 20))
        self.scheduler = APScheduler(
            threadpool=self.pool,
            job_defaults={
                'coalesce': True,
                'misfire_grace_time': 30
            }
        )

        self.load_plugins()

    def execute_scheduler(self):
        # Schedule a daily job to cleanup stuff thats been left around (eip's with no instances etc)
        self.scheduler.add_job(
            self.cleanup,
            trigger='cron',
            name='cleanup',
            hour=3,
            minute=0,
            second=0
        )

        # Schedule periodic scheduling of jobs
        self.scheduler.add_job(
            self.schedule_jobs,
            trigger='interval',
            name='schedule_jobs',
            seconds=60,
            start_date=datetime.now() + timedelta(seconds=1)
        )

        # Periodically reload the dbconfiguration
        self.scheduler.add_job(
            self.dbconfig.reload_data,
            trigger='interval',
            name='reload_dbconfig',
            minutes=5,
            start_date=datetime.now() + timedelta(seconds=3)
        )

        self.scheduler.start()

    def execute_worker(self):
        """This method is not used for the standalone scheduler."""
        print('The standalone scheduler does not have a separate worker model. '
              'Executing the scheduler will also execute the workers')

    def schedule_jobs(self):
        current_jobs = {
            x.name: x for x in self.scheduler.get_jobs() if x.name not in (
                'cleanup',
                'schedule_jobs',
                'reload_dbconfig'
            )
        }
        new_jobs = []
        start = datetime.now() + timedelta(seconds=1)
        _, accounts = BaseAccount.search(include_disabled=False)

        # region Global collectors (non-aws)
        if CollectorType.GLOBAL in self.collectors:
            for wkr in self.collectors[CollectorType.GLOBAL]:
                job_name = 'global_{}'.format(wkr.name)
                new_jobs.append(job_name)

                if job_name in current_jobs:
                    continue

                self.scheduler.add_job(
                    self.execute_global_worker,
                    trigger='interval',
                    name=job_name,
                    minutes=wkr.interval,
                    start_date=start,
                    args=[wkr],
                    kwargs={}
                )

                start += timedelta(seconds=30)
        # endregion

        # region AWS collectors
        aws_accounts = list(filter(lambda x: x.account_type == AWSAccount.account_type, accounts))
        for acct in aws_accounts:
            if CollectorType.AWS_ACCOUNT in self.collectors:
                for wkr in self.collectors[CollectorType.AWS_ACCOUNT]:
                    job_name = '{}_{}'.format(acct.account_name, wkr.name)
                    new_jobs.append(job_name)

                    if job_name in current_jobs:
                        continue

                    self.scheduler.add_job(
                        self.execute_aws_account_worker,
                        trigger='interval',
                        name=job_name,
                        minutes=wkr.interval,
                        start_date=start,
                        args=[wkr],
                        kwargs={'account': acct.account_name}
                    )

            if CollectorType.AWS_REGION in self.collectors:
                for wkr in self.collectors[CollectorType.AWS_REGION]:
                    for region in AWS_REGIONS:
                        job_name = '{}_{}_{}'.format(acct.account_name, region, wkr.name)
                        new_jobs.append(job_name)

                        if job_name in current_jobs:
                            continue

                        self.scheduler.add_job(
                            self.execute_aws_region_worker,
                            trigger='interval',
                            name=job_name,
                            minutes=wkr.interval,
                            start_date=start,
                            args=[wkr],
                            kwargs={'account': acct.account_name, 'region': region}
                        )
            db.session.commit()
            start += timedelta(seconds=self.dbconfig.get('worker_interval', self.ns, 30))
        # endregion

        # region Auditors
        start = datetime.now() + timedelta(seconds=1)
        for wkr in self.auditors:
            job_name = 'auditor_{}'.format(wkr.name)
            new_jobs.append(job_name)

            if job_name in current_jobs:
                continue

            if app_config.log_level == 'DEBUG':
                audit_start = start + timedelta(seconds=5)
            else:
                audit_start = start + timedelta(minutes=5)

            self.scheduler.add_job(
                self.execute_auditor_worker,
                trigger='interval',
                name=job_name,
                minutes=wkr.interval,
                start_date=audit_start,
                args=[wkr],
                kwargs={}
            )
            start += timedelta(seconds=self.dbconfig.get('worker_interval', self.ns, 30))
        # endregion

        extra_jobs = list(set(current_jobs) - set(new_jobs))
        for job in extra_jobs:
            self.log.warning('Removing job {} as it is no longer needed'.format(job))
            current_jobs[job].remove()

    def execute_global_worker(self, data, **kwargs):
        try:
            cls = self.get_class_from_ep(data.entry_point)
            worker = cls(**kwargs)
            self.log.info('RUN_INFO: {} starting at {}, next run will be at approximately {}'.format(data.entry_point['module_name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (datetime.now() + timedelta(minutes=data.interval)).strftime("%Y-%m-%d %H:%M:%S")))
            self.log.info('Starting global {} worker'.format(data.name))
            worker.run()

        except Exception as ex:
            self.log.exception('Global Worker {}: {}'.format(data.name, ex))

        finally:
            db.session.rollback()
            self.log.info('Completed run for global {} worker'.format(data.name))

    def execute_aws_account_worker(self, data, **kwargs):
        try:
            cls = self.get_class_from_ep(data.entry_point)
            worker = cls(**kwargs)
            self.log.info('RUN_INFO: {} starting at {}, next run will be at approximately {}'.format(data.entry_point['module_name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (datetime.now() + timedelta(minutes=data.interval)).strftime("%Y-%m-%d %H:%M:%S")))
            worker.run()

        except Exception as ex:
            self.log.exception('AWS Account Worker {}/{}: {}'.format(data.name, kwargs['account'], ex))

        finally:
            db.session.rollback()
            self.log.info('Completed run for {} worker on {}'.format(data.name, kwargs['account']))

    def execute_aws_region_worker(self, data, **kwargs):
        try:
            cls = self.get_class_from_ep(data.entry_point)
            worker = cls(**kwargs)
            self.log.info('RUN_INFO: {} starting at {} for account {} / region {}, next run will be at approximately {}'.format(data.entry_point['module_name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kwargs['account'], kwargs['region'], (datetime.now() + timedelta(minutes=data.interval)).strftime("%Y-%m-%d %H:%M:%S")))
            worker.run()

        except Exception as ex:
            self.log.exception('AWS Region Worker {}/{}/{}: {}'.format(
                data.name,
                kwargs['account'],
                kwargs['region'],
                ex
            ))

        finally:
            db.session.rollback()
            self.log.info('Completed run for {} worker on {}/{}'.format(
                data.name,
                kwargs['account'],
                kwargs['region']
            ))

    def execute_auditor_worker(self, data, **kwargs):
        try:
            cls = self.get_class_from_ep(data.entry_point)
            worker = cls(**kwargs)
            self.log.info('RUN_INFO: {} starting at {}, next run will be at approximately {}'.format(data.entry_point['module_name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (datetime.now() + timedelta(minutes=data.interval)).strftime("%Y-%m-%d %H:%M:%S")))
            worker.run()

        except Exception as ex:
            self.log.exception('Auditor Worker {}: {}'.format(data.name, ex))

        finally:
            db.session.rollback()
            self.log.info('Completed run for auditor {}'.format(data.name))

    def cleanup(self):
        try:
            self.log.info('Running cleanup tasks')

            log_purge_date = datetime.now() - timedelta(days=self.dbconfig.get('log_keep_days', 'log', default=31))
            db.LogEvent.find(LogEvent.timestamp < log_purge_date)

            db.session.commit()
        finally:
            db.session.rollback()
