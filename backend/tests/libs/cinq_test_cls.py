from cinq_auditor_domain_hijacking import DomainHijackAuditor

from cinq_auditor_ebs import EBSAuditor

from cinq_auditor_required_tags import RequiredTagsAuditor


class MockNotify(object):
    def notify(self, notices):
        self._cinq_test_notices = notices


class MockDomainHijackAuditor(MockNotify, DomainHijackAuditor):
    pass


class MockEBSAuditor(MockNotify, EBSAuditor):
    pass


class MockRequiredTagsAuditor(MockNotify, RequiredTagsAuditor):
    pass
