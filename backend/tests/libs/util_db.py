import logging

from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST
from cloud_inquisitor.database import db
from cloud_inquisitor.schema import Resource, ResourceProperty, IssueProperty, Issue
from tests.libs.var_const import CINQ_TEST_REGION

logger = logging.getLogger(__name__)


def empty_tables(*args):
    for table in args:
        db.session.query(table).delete()

    db.session.commit()


def get_issue(issue_id):
    try:
        qry = db.session.query(Issue).filter(Issue.issue_id == issue_id).first()
        return qry[0]
    except IndexError:
        return None


def has_resource(resource_id):
    return bool(db.session.query(Resource).filter(Resource.resource_id == resource_id).first())


def get_resource(resource_id):
    try:
        qry = db.session.query(Resource).filter(Resource.resource_id == resource_id).first()
        return qry[0]
    except IndexError:
        return None


def create_resource(
        resource_type,
        resource_id,
        account_id,
        properties=None,
        tags=None,
        location=CINQ_TEST_REGION,
        auto_add=True,
        auto_commit=False
):
    return resource_type.create(
        resource_id,
        account_id=account_id,
        properties=properties,
        tags=tags,
        location=location,
        auto_add=auto_add,
        auto_commit=auto_commit
    )


def modify_issue(issue_id, issue_property, value):
    try:
        issue = db.IssueProperty.filter(
            IssueProperty.issue_id == issue_id, IssueProperty.name == issue_property
        ).first()
        if not issue:
            return False
        else:
            issue.value = value
            db.session.commit()
            return True
    except Exception as e:
        logger.error('Failed to modify issue property {}: {}'.format(issue_property, e))
    finally:
        db.session.rollback()


def modify_resource(resource_id, resource_property, value):
    try:
        resource = db.ResourceProperty.filter(
            ResourceProperty.resource_id == resource_id, ResourceProperty.name == resource_property
        ).first()
        if not resource:
            return False
        else:
            resource.value = value
            db.session.commit()
            return True
    except Exception as e:
        logger.error('Failed to modify resource property {}: {}'.format(resource_property, e))
    finally:
        db.session.rollback()


def set_tags(resource, tags):
    for k, v in tags.items():
        resource.set_tag(k, v)

    db.session.commit()


def set_test_user_role(role):
    dbconfig.set(NS_CINQ_TEST, 'user_role', role)
