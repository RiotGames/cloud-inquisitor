import json
from datetime import datetime, timedelta
from uuid import uuid4

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler as APScheduler
from botocore.exceptions import ClientError
from cloud_inquisitor import app_config, get_local_aws_session, AWS_REGIONS
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.constants import NS_SCHEDULER_SQS, SchedulerStatus
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import InquisitorError, SchedulerError
from cloud_inquisitor.plugins import CollectorType, BaseScheduler
from cloud_inquisitor.plugins.types.accounts import BaseAccount, AWSAccount
from cloud_inquisitor.schema.base import SchedulerBatch, SchedulerJob
from cloud_inquisitor.utils import get_hash
from cloud_inquisitor.wrappers import retry


class SQSScheduler(BaseScheduler):
    name = 'SQS Scheduler'
    ns = NS_SCHEDULER_SQS
    options = (
        ConfigOption('queue_region', 'us-west-2', 'string', 'Region of the SQS Queues'),
        ConfigOption('job_queue_url', '', 'string', 'URL of the SQS Queue for pending jobs'),
        ConfigOption('status_queue_url', '', 'string', 'URL of the SQS Queue for worker reports'),
        ConfigOption('job_delay', 2, 'float', 'Time between each scheduled job, in seconds. Can be used to '
                     'avoid spiky load during execution of tasks'),
    )

    def __init__(self):
        """Initialize the SQSScheduler, setting up the process pools, scheduler and connecting to the required
        SQS Queues"""
        super().__init__()

        self.pool = ProcessPoolExecutor(1)
        self.scheduler = APScheduler(
            threadpool=self.pool,
            job_defaults={
                'coalesce': True,
                'misfire_grace_time': 30
            }
        )

        session = get_local_aws_session()
        sqs = session.resource('sqs', self.dbconfig.get('queue_region', self.ns))

        self.job_queue = sqs.Queue(self.dbconfig.get('job_queue_url', self.ns))
        self.status_queue = sqs.Queue(self.dbconfig.get('status_queue_url', self.ns))

    def execute_scheduler(self):
        """Main entry point for the scheduler. This method will start two scheduled jobs, `schedule_jobs` which takes
         care of scheduling the actual SQS messaging and `process_status_queue` which will track the current status
         of the jobs as workers are executing them

        Returns:
            `None`
        """
        try:
            # Schedule periodic scheduling of jobs
            self.scheduler.add_job(
                self.schedule_jobs,
                trigger='interval',
                name='schedule_jobs',
                minutes=15,
                start_date=datetime.now() + timedelta(seconds=1)
            )

            self.scheduler.add_job(
                self.process_status_queue,
                trigger='interval',
                name='process_status_queue',
                seconds=30,
                start_date=datetime.now() + timedelta(seconds=5),
                max_instances=1
            )

            self.scheduler.start()

        except KeyboardInterrupt:
            self.scheduler.shutdown()

    def list_current_jobs(self):
        """Return a list of the currently scheduled jobs in APScheduler

        Returns:
            `dict` of `str`: :obj:`apscheduler/job:Job`
        """
        jobs = {}
        for job in self.scheduler.get_jobs():
            if job.name not in ('schedule_jobs', 'process_status_queue'):
                jobs[job.name] = job

        return jobs

    def schedule_jobs(self):
        """Schedule or remove jobs as needed.

        Checks to see if there are any jobs that needs to be scheduled, after refreshing the database configuration
        as well as the list of collectors and auditors.

        Returns:
            `None`
        """
        self.dbconfig.reload_data()
        self.collectors = {}
        self.auditors = []
        self.load_plugins()

        _, accounts = BaseAccount.search(include_disabled=False)
        current_jobs = self.list_current_jobs()
        new_jobs = []
        batch_id = str(uuid4())

        batch = SchedulerBatch()
        batch.batch_id = batch_id
        batch.status = SchedulerStatus.PENDING
        db.session.add(batch)
        db.session.commit()

        start = datetime.now() + timedelta(seconds=1)
        job_delay = dbconfig.get('job_delay', self.ns, 0.5)

        # region Global collectors (non-aws)
        if CollectorType.GLOBAL in self.collectors:
            for worker in self.collectors[CollectorType.GLOBAL]:
                job_name = get_hash(worker)

                if job_name in current_jobs:
                    continue

                self.scheduler.add_job(
                    self.send_worker_queue_message,
                    trigger='interval',
                    name=job_name,
                    minutes=worker.interval,
                    start_date=start,
                    kwargs={
                        'batch_id': batch_id,
                        'job_name': job_name,
                        'entry_point': worker.entry_point,
                        'worker_args': {}
                    }
                )
                start += timedelta(seconds=job_delay)
        # endregion

        # region AWS collectors
        aws_accounts = list(filter(lambda x: x.account_type == AWSAccount.account_type, accounts))
        if CollectorType.AWS_ACCOUNT in self.collectors:
            for worker in self.collectors[CollectorType.AWS_ACCOUNT]:
                for account in aws_accounts:
                    job_name = get_hash((account.account_name, worker))
                    if job_name in current_jobs:
                        continue

                    new_jobs.append(job_name)

                    self.scheduler.add_job(
                        self.send_worker_queue_message,
                        trigger='interval',
                        name=job_name,
                        minutes=worker.interval,
                        start_date=start,
                        kwargs={
                            'batch_id': batch_id,
                            'job_name': job_name,
                            'entry_point': worker.entry_point,
                            'worker_args': {
                                'account': account.account_name
                            }
                        }
                    )
                    start += timedelta(seconds=job_delay)

        if CollectorType.AWS_REGION in self.collectors:
            for worker in self.collectors[CollectorType.AWS_REGION]:
                for region in AWS_REGIONS:
                    for account in aws_accounts:
                        job_name = get_hash((account.account_name, region, worker))

                        if job_name in current_jobs:
                            continue

                        new_jobs.append(job_name)

                        self.scheduler.add_job(
                            self.send_worker_queue_message,
                            trigger='interval',
                            name=job_name,
                            minutes=worker.interval,
                            start_date=start,
                            kwargs={
                                'batch_id': batch_id,
                                'job_name': job_name,
                                'entry_point': worker.entry_point,
                                'worker_args': {
                                    'account': account.account_name,
                                    'region': region
                                }
                            }
                        )
                        start += timedelta(seconds=job_delay)
        # endregion

        # region Auditors
        if app_config.log_level == 'DEBUG':
            audit_start = start + timedelta(seconds=5)
        else:
            audit_start = start + timedelta(minutes=5)

        for worker in self.auditors:
            job_name = get_hash((worker,))
            if job_name in current_jobs:
                continue

            new_jobs.append(job_name)

            self.scheduler.add_job(
                self.send_worker_queue_message,
                trigger='interval',
                name=job_name,
                minutes=worker.interval,
                start_date=audit_start,
                kwargs={
                    'batch_id': batch_id,
                    'job_name': job_name,
                    'entry_point': worker.entry_point,
                    'worker_args': {}
                }
            )
            audit_start += timedelta(seconds=job_delay)
        # endregion

    def send_worker_queue_message(self, *, batch_id, job_name, entry_point, worker_args, retry_count=0):
        """Send a message to the `worker_queue` for a worker to execute the requests job

        Args:
            batch_id (`str`): Unique ID of the batch the job belongs to
            job_name (`str`): Non-unique ID of the job. This is used to ensure that the same job is only scheduled
            a single time per batch
            entry_point (`dict`): A dictionary providing the entry point information for the worker to load the class
            worker_args (`dict`): A dictionary with the arguments required by the worker class (if any, can be an
            empty dictionary)
            retry_count (`int`): The number of times this one job has been attempted to be executed. If a job fails to
            execute after 3 retries it will be marked as failed

        Returns:
            `None`
        """
        try:
            job_id = str(uuid4())
            self.job_queue.send_message(
                MessageBody=json.dumps({
                    'batch_id': batch_id,
                    'job_id': job_id,
                    'job_name': job_name,
                    'entry_point': entry_point,
                    'worker_args': worker_args,
                }),
                MessageDeduplicationId=job_id,
                MessageGroupId=batch_id,
                MessageAttributes={
                    'RetryCount': {
                        'StringValue': str(retry_count),
                        'DataType': 'Number'

                    }
                }
            )

            if retry_count == 0:
                job = SchedulerJob()
                job.job_id = job_id
                job.batch_id = batch_id
                job.status = SchedulerStatus.PENDING
                job.data = worker_args

                db.session.add(job)
                db.session.commit()
        except:
            self.log.exception('Error when processing worker task')

    def execute_worker(self):
        """Retrieve a message from the `worker_queue` and process the request.

        This function will read a single message from the `worker_queue` and load the specified `EntryPoint`
        and execute the worker with the provided arguments. Upon completion (failure or otherwise) a message is sent
        to the `status_queue` information the scheduler about the return status (success/failure) of the worker

        Returns:
            `None`
        """
        try:
            try:
                messages = self.job_queue.receive_messages(
                    MaxNumberOfMessages=1,
                    MessageAttributeNames=('RetryCount',)
                )

            except ClientError:
                self.log.exception('Failed fetching messages from SQS queue')
                return

            if not messages:
                self.log.debug('No pending jobs')
                return

            for message in messages:
                try:
                    retry_count = int(message.message_attributes['RetryCount']['StringValue'])

                    data = json.loads(message.body)
                    try:
                        # SQS FIFO queues will not allow another thread to get any new messages until the messages
                        # in-flight are returned to the queue or deleted, so we remove the message from the queue as
                        # soon as we've loaded the data
                        self.send_status_message(data['job_id'], SchedulerStatus.STARTED)
                        message.delete()

                        cls = self.get_class_from_ep(data['entry_point'])
                        worker = cls(**data['worker_args'])
                        if hasattr(worker, 'type'):
                            if worker.type == CollectorType.GLOBAL:
                                self.log.info('RUN_INFO: {} starting at {}, next run will be at approximately {}'.format(data['entry_point']['module_name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (datetime.now() + timedelta(minutes=worker.interval)).strftime("%Y-%m-%d %H:%M:%S")))
                            elif worker.type == CollectorType.AWS_REGION:
                                self.log.info('RUN_INFO: {} starting at {} for account {} / region {}, next run will be at approximately {}'.format(data['entry_point']['module_name'],	datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['worker_args']['account'], data['worker_args']['region'], (datetime.now() + timedelta(minutes=worker.interval)).strftime("%Y-%m-%d %H:%M:%S")))
                            elif worker.type == CollectorType.AWS_ACCOUNT:
                                self.log.info('RUN_INFO: {} starting at {} for account {} next run will be at approximately {}'.format(data['entry_point']['module_name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['worker_args']['account'], (datetime.now() + timedelta(minutes=worker.interval)).strftime("%Y-%m-%d %H:%M:%S")))
                        else:
                            self.log.info('RUN_INFO: {} starting at {} next run will be at approximately {}'.format(data['entry_point']['module_name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (datetime.now() + timedelta(minutes=worker.interval)).strftime("%Y-%m-%d %H:%M:%S")))
                        worker.run()

                        self.send_status_message(data['job_id'], SchedulerStatus.COMPLETED)
                    except InquisitorError:
                        # If the job failed for some reason, reschedule it unless it has already been retried 3 times
                        if retry_count >= 3:
                            self.send_status_message(data['job_id'], SchedulerStatus.FAILED)
                        else:
                            self.send_worker_queue_message(
                                batch_id=data['batch_id'],
                                job_name=data['job_name'],
                                entry_point=data['entry_point'],
                                worker_args=data['worker_args'],
                                retry_count=retry_count + 1
                            )
                except:
                    self.log.exception('Failed processing scheduler job: {}'.format(message.body))

        except KeyboardInterrupt:
            self.log.info('Shutting down worker thread')


    @retry
    def send_status_message(self, object_id, status):
        """Send a message to the `status_queue` to update a job's status.

        Returns `True` if the message was sent, else `False`

        Args:
            object_id (`str`): ID of the job that was executed
            status (:obj:`SchedulerStatus`): Status of the job

        Returns:
            `bool`
        """
        try:
            body = json.dumps({
                'id': object_id,
                'status': status
            })

            self.status_queue.send_message(
                MessageBody=body,
                MessageGroupId='job_status',
                MessageDeduplicationId=get_hash((object_id, status))
            )
            return True
        except Exception as ex:
            print(ex)
            return False

    @retry
    def process_status_queue(self):
        """Process all messages in the `status_queue` and check for any batches that needs to change status

        Returns:
            `None`
        """
        self.log.debug('Start processing status queue')
        while True:
            messages = self.status_queue.receive_messages(MaxNumberOfMessages=10)

            if not messages:
                break

            for message in messages:
                data = json.loads(message.body)
                job = SchedulerJob.get(data['id'])
                try:
                    if job and job.update_status(data['status']):
                        db.session.commit()
                except SchedulerError as ex:
                    if hasattr(ex, 'message') and ex.message == 'Attempting to update already completed job':
                        pass

                message.delete()

        # Close any batch that is now complete
        open_batches = db.SchedulerBatch.find(SchedulerBatch.status < SchedulerStatus.COMPLETED)
        for batch in open_batches:
            open_jobs = list(filter(lambda x: x.status < SchedulerStatus.COMPLETED, batch.jobs))
            if not open_jobs:
                open_batches.remove(batch)
                batch.update_status(SchedulerStatus.COMPLETED)
                self.log.debug('Closed completed batch {}'.format(batch.batch_id))
            else:
                started_jobs = list(filter(lambda x: x.status > SchedulerStatus.PENDING, open_jobs))
                if batch.status == SchedulerStatus.PENDING and len(started_jobs) > 0:
                    batch.update_status(SchedulerStatus.STARTED)
                    self.log.debug('Started batch manually {}'.format(batch.batch_id))

        # Check for stale batches / jobs
        for batch in open_batches:
            if batch.started < datetime.now() - timedelta(hours=2):
                self.log.warning('Closing a stale scheduler batch: {}'.format(batch.batch_id))
                for job in batch.jobs:
                    if job.status < SchedulerStatus.COMPLETED:
                        job.update_status(SchedulerStatus.ABORTED)
                batch.update_status(SchedulerStatus.ABORTED)
        db.session.commit()
