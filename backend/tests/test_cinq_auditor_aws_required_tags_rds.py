import datetime
import random
import uuid

from cloud_inquisitor.constants import AuditActions
from cloud_inquisitor.plugins.types.resources import RDSInstance
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.lib_cinq_auditor_aws_required_tags import prep_rds_testing, VALID_TAGS, STANDARD_ALERT_SETTINGS_STOP
from tests.libs.util_cinq import setup_test_aws
from tests.libs.util_db import create_resource, set_tags


def test_rds_generic(cinq_test_service):
    """
    1. We will generate batch of compliant and non-compliant RDS resources, run the auditor and check if it works as
        expected
    2. We will make random non-compliant RDS instance meets the FIXED, STOP or REMOVE criteria and check if it works as
        expected
    """
    # Prep
    setup_info = setup_test_aws(cinq_test_service)
    recipient = setup_info['recipient']
    account = setup_info['account']
    compliant_resources = []
    non_compliant_resources = []

    prep_rds_testing(cinq_test_service)

    # Add resources
    num_resources = 50

    for i in range(0, num_resources):
        compliance_selector = random.randint(0, 1)
        if compliance_selector:
            tags = VALID_TAGS
        else:
            tags = {}

        new_resource = create_resource(
            resource_type=RDSInstance,
            resource_id=uuid.uuid4().hex,
            account_id=account.account_id,
            properties={
                'creation_date': datetime.datetime(2000, 1, 1),
                'metrics': {}
            },
            tags=tags,
            auto_add=True,
            auto_commit=True
        )

        if compliance_selector:
            compliant_resources.append(new_resource.id)
        else:
            non_compliant_resources.append(new_resource.id)

    # Initialize auditor
    auditor = MockRequiredTagsAuditor()
    auditor.run(enable_process_action=False)

    issue_not_fixed = auditor._cinq_test_notices[recipient]['not_fixed']

    for item in issue_not_fixed:
        assert item['resource'].id not in compliant_resources
        assert item['resource'].id in non_compliant_resources
        assert item['action'] == AuditActions.ALERT

    resources_to_terminate = []
    resources_to_stop = []
    resources_fixed = []

    for item in issue_not_fixed:
        mock_selector = random.randint(0, 3)

        if mock_selector == 3:
            # Mock resources that should be terminated
            cinq_test_service.modify_issue(
                item['issue'].id,
                'created',
                0
            )
            resources_to_terminate.append(item['resource'].id)

        elif mock_selector == 2:
            # Mock resources that should be stopped
            cinq_test_service.modify_issue(
                item['issue'].id,
                'created',
                item['issue'].created - STANDARD_ALERT_SETTINGS_STOP - 1
            )
            resources_to_stop.append(item['resource'].id)
        elif mock_selector == 1:
            set_tags(item['resource'], VALID_TAGS)
            resources_fixed.append(item['resource'].id)
        else:
            # Leave the issue as-is
            pass

    auditor.run(enable_process_action=False)
    issue_not_fixed = auditor._cinq_test_notices[recipient]['not_fixed']
    issue_fixed = auditor._cinq_test_notices[recipient]['fixed']

    for item in issue_not_fixed:
        if item['action'] == AuditActions.STOP:
            resources_to_stop.remove(item['resource'].id)
        elif item['action'] == AuditActions.REMOVE:
            resources_to_terminate.remove(item['resource'].id)

    for item in issue_fixed:
        resources_fixed.remove(item['resource'].resource_id)

    assert resources_to_stop == []
    assert resources_to_terminate == []
    assert resources_fixed == []


def test_rds_corrupted_data(cinq_test_service):
    # Prep
    setup_info = setup_test_aws(cinq_test_service)
    recipient = setup_info['recipient']
    account = setup_info['account']

    auditor = MockRequiredTagsAuditor()

    new_resource = create_resource(
        resource_type=RDSInstance,
        resource_id=uuid.uuid4().hex,
        account_id=account.account_id,
        properties={},
        tags={},
        auto_add=True,
        auto_commit=True
    )

    auditor.run(enable_process_action=False)
    assert auditor._cinq_test_notices == {}
