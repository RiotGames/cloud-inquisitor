from sqlalchemy import distinct

from cloud_inquisitor.constants import ROLE_ADMIN
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import AuditLog
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import rollback, check_auth


class AuditLogList(BaseView):
    URLS = ['/api/v1/auditlog']
    MENU_ITEMS = [
        MenuItem(
            'admin',
            'Audit Log',
            'auditlog.list',
            'auditlog',
            args={
                'page': 1,
                'count': 100,
                'events': [],
                'actors': []
            },
            order=80
        )
    ]

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self):
        self.reqparse.add_argument('page', type=int, default=1)
        self.reqparse.add_argument('count', type=int, default=100)
        self.reqparse.add_argument('events', type=str, action='append', default=None)
        self.reqparse.add_argument('actors', type=str, action='append', default=None)
        args = self.reqparse.parse_args()

        qry = db.AuditLog.order_by(AuditLog.audit_log_event_id.desc())
        if args['events']:
            qry = qry.filter(AuditLog.event.in_(args['events']))

        if args['actors']:
            qry = qry.filter(AuditLog.actor.in_(args['actors']))

        totalEvents = qry.count()
        qry = qry.limit(args['count'])

        if (args['page'] - 1) > 0:
            offset = (args['page'] - 1) * args['count']
            qry = qry.offset(offset)

        return self.make_response({
            'auditLogEvents': qry.all(),
            'auditLogEventCount': totalEvents,
            'eventTypes': [x[0] for x in db.query(distinct(AuditLog.event)).all()]
        })


class AuditLogGet(BaseView):
    URLS = ['/api/v1/auditlog/<int:auditLogEventId>']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self, auditLogEventId):
        event = db.AuditLog.find_one(AuditLog.audit_log_event_id == auditLogEventId)

        return self.make_response({
            'auditLogEvent': event
        })
