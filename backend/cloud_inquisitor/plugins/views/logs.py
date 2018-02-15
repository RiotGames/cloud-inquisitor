from datetime import datetime, timedelta

from flask import session
from sqlalchemy import func, desc

from cloud_inquisitor.constants import ROLE_ADMIN
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import LogEvent, AuditLog
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback


class Logs(BaseView):
    URLS = ['/api/v1/logs']
    MENU_ITEMS = [
        MenuItem(
            'admin',
            'Logs',
            'log.list',
            'log',
            args={
                'page': 1,
                'count': 100,
                'levelno': None
            },
            order=90
        )
    ]

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self):
        self.reqparse.add_argument('count', type=int, default=100)
        self.reqparse.add_argument('page', type=int, default=0)
        self.reqparse.add_argument('levelno', type=int, default=0)
        args = self.reqparse.parse_args()

        if args['levelno'] > 0:
            total_events = db.query(
                func.count(LogEvent.log_event_id)
            ).filter(LogEvent.levelno >= args['levelno']).first()[0]

            qry = (
                db.LogEvent
                .filter(LogEvent.levelno >= args['levelno'])
                .order_by(desc(LogEvent.timestamp))
                .limit(args['count'])
            )
        else:
            total_events = db.query(func.count(LogEvent.log_event_id)).first()[0]
            qry = (
                db.LogEvent
                .order_by(desc(LogEvent.timestamp))
                .limit(args['count'])
            )

        if (args['page'] - 1) > 0:
            offset = (args['page'] - 1) * args['count']
            qry = qry.offset(offset)

        events = qry.all()
        return self.make_response({
            'logEventCount': total_events,
            'logEvents': events
        })

    @rollback
    @check_auth(ROLE_ADMIN)
    def delete(self):
        self.reqparse.add_argument('maxAge', type=int, default=31)
        args = self.reqparse.parse_args()
        AuditLog.log('logs.prune', session['user'].username, args)

        db.LogEvent.filter(
            func.datesub(
                LogEvent.timestamp < datetime.now() - timedelta(days=args['maxAge'])
            )
        ).delete()

        db.session.commit()


class LogDetails(BaseView):
    URLS = ['/api/v1/logs/<int:logEventId>']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self, logEventId):
        evt = db.LogEvent.find_one(LogEvent.log_event_id == logEventId)

        return self.make_response({'logEvent': evt})
