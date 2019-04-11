import datetime
import random
import uuid

from cloud_inquisitor.constants import AuditActions
from cloud_inquisitor.plugins.types.resources import RDSInstance
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.lib_cinq_auditor_aws_required_tags import prep_rds_testing, VALID_TAGS, STANDARD_ALERT_SETTINGS_STOP
from tests.libs.util_cinq import setup_test_aws
from tests.libs.util_db import create_resource


def test_rds_generic(cinq_test_service):
    """
    Test will pass if for an S3 bucket meet the following condition:
        - Bucket is empty
        - No Bucket Policy was set
        - No Lifecycle Policy was set
        - No tag was set

    The Auditor will:
        - Detect non-compliant S3 buckets
        - Respect grace period settings
        - Be able to remove an empty bucket successfully when the "REMOVE" criteria are met
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

    for item in issue_not_fixed:
        mock_selector = random.randint(0, 2)

        if mock_selector == 2:
            # Mock resources that should be terminated
            cinq_test_service.modify_issue(
                item['issue'].id,
                'created',
                0
            )
            resources_to_terminate.append(item['resource'].id)

        elif mock_selector == 1:
            # Mock resources that should be stopped
            cinq_test_service.modify_issue(
                item['issue'].id,
                'created',
                item['issue'].created - STANDARD_ALERT_SETTINGS_STOP - 1
            )
            resources_to_stop.append(item['resource'].id)
        else:
            # Leave the issue as-is
            pass

    auditor.run(enable_process_action=False)
    issue_not_fixed = auditor._cinq_test_notices[recipient]['not_fixed']

    for item in issue_not_fixed:
        if item['action'] == AuditActions.STOP:
            resources_to_stop.remove(item['resource'].id)
        elif item['action'] == AuditActions.REMOVE:
            resources_to_terminate.remove(item['resource'].id)

    assert resources_to_stop == []
    assert resources_to_terminate == []


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
