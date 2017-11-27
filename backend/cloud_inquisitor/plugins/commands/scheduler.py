import time
import threading

from flask_script import Option
from pkg_resources import iter_entry_points

from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_SCHEDULER
from cloud_inquisitor.plugins.commands import BaseCommand


class BaseSchedulerCommand(BaseCommand):
    ns = NS_SCHEDULER
    option_list = [
        Option('--scheduler', dest='scheduler', metavar='name', type=str,
               help='Overrides the scheduler configured in the UI'),
        Option('--list', dest='list', action='store_true', default=False,
               help='List the available schedulers'),

    ]

    def __init__(self):
        super().__init__()
        self.scheduler_plugins = self.load_scheduler_plugins()
        self.active_scheduler = dbconfig.get('scheduler')

    def load_scheduler_plugins(self):
        """Refresh the list of available schedulers

        Returns:
            `list` of :obj:`BaseScheduler`
        """
        schedulers = {}
        for ep in iter_entry_points('cloud_inquisitor.plugins.schedulers'):
            cls = ep.load()
            if cls.enabled:
                self.log.debug('Scheduler loaded: {} in module {}'.format(cls.__name__, cls.__module__))
                schedulers[cls.__name__] = cls
            else:
                self.log.debug('Scheduler disabled: {} in module {}'.format(cls.__name__, cls.__module__))

        return schedulers

    def run(self, **kwargs):
        if kwargs['list']:
            self.log.info('--- List of Scheduler Modules ---')
            for name, scheduler in list(self.scheduler_plugins.items()):
                if self.active_scheduler == name:
                    self.log.info('{} (active)'.format(name))
                else:
                    self.log.info(name)
            self.log.info('--- End list of Scheduler Modules ---')
            return

        if kwargs['scheduler']:
            self.active_scheduler = kwargs['scheduler']

        if self.active_scheduler not in self.scheduler_plugins:
            self.log.error('Unable to locate the {} scheduler plugin'.format(self.active_scheduler))
            return


class Scheduler(BaseSchedulerCommand):
    """Execute the selected scheduler"""
    name = 'Scheduler'

    def run(self, **kwargs):
        """Execute the scheduler.

        Returns:
            `None`
        """
        super().run(**kwargs)

        scheduler = self.scheduler_plugins[self.active_scheduler]()
        scheduler.execute_scheduler()

class Worker(BaseSchedulerCommand):
    """Execute the selected worker"""
    name = 'Worker'
    option_list = BaseSchedulerCommand.option_list + [
        Option('--no-daemon', default=False, action='store_true',
               help='Do not execute in daemon mode (if supported). Execution stops as soon as the worker returns'),
        Option('--delay', default=10, type=int,
               help='Delay between executions in daemon mode, in seconds. Default: 10'),
        Option('--threads', default=5, type=int,
               help='Number of worker threads to spawn. --no-daemon only uses a single thread. Default: 5'),
    ]

    def run(self, **kwargs):
        """Execute the worker thread.

        Returns:
            `None`
        """
        super().run(**kwargs)
        scheduler = self.scheduler_plugins[self.active_scheduler]()

        if not kwargs['no_daemon']:
            self.log.info('Starting {} worker with {} threads checking for new messages every {} seconds'.format(
                scheduler.name,
                kwargs['threads'],
                kwargs['delay']
            ))

            for i in range(kwargs['threads']):
                thd = threading.Thread(
                    target=self.execute_worker_thread,
                    args=(scheduler.execute_worker, kwargs['delay'])
                )
                thd.start()
        else:
            self.log.info('Starting {} worker for a single non-daemon execution'.format(
                scheduler.name
            ))
            scheduler.execute_worker()

    def execute_worker_thread(self, func, delay):
        while True:
            func()
            time.sleep(delay)
