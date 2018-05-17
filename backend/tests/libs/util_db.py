from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST
from cloud_inquisitor.database import db
from cloud_inquisitor.schema import Resource, ResourceProperty


def empty_tables(*args):
    for table in args:
        db.session.query(table).delete()

    db.session.commit()


def has_resource(resource_id):
    return bool(db.session.query(Resource).filter(Resource.resource_id == resource_id).first())


def get_resource(resource_id):
    try:
        qry = db.session.query(Resource).filter(Resource.resource_id == resource_id).first()
        return qry[0]
    except IndexError:
        return None


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
    finally:
        db.session.rollback()


def set_test_user_role(role):
    dbconfig.set(NS_CINQ_TEST, 'user_role', role)
