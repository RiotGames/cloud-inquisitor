from cinq_auditor_domain_hijacking import DomainHijackAuditor

from cinq_auditor_ebs import EBSAuditor

from cinq_auditor_required_tags import RequiredTagsAuditor
from cloud_inquisitor.constants import ActionStatus


class MockNotify(object):
    def notify(self, notices):
        self._cinq_test_notices = notices


class MockDomainHijackAuditor(MockNotify, DomainHijackAuditor):
    pass


class MockEBSAuditor(MockNotify, EBSAuditor):
    pass


class MockRequiredTagsAuditor(MockNotify, RequiredTagsAuditor):
    def run(self, enable_process_action=True, *args, **kwargs):
        if not enable_process_action:
            self.process_action = lambda resource, action: ActionStatus.SUCCEED

        super().run(args, kwargs)
