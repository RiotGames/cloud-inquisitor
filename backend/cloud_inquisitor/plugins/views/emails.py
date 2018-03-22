from flask import session
from sqlalchemy import desc, func, distinct

from cloud_inquisitor.constants import ROLE_ADMIN, HTTP
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import EmailSendError
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import Email
from cloud_inquisitor.utils import MenuItem, send_notification, NotificationContact
from cloud_inquisitor.wrappers import check_auth, rollback


class EmailList(BaseView):
    URLS = ['/api/v1/emails']
    MENU_ITEMS = [
        MenuItem(
            'admin',
            'Emails',
            'email.list',
            'email',
            args={
                'page': 1,
                'count': 100,
                'subsystem': None
            },
            order=70
        )
    ]

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self):
        self.reqparse.add_argument('page', type=int, default=1)
        self.reqparse.add_argument('count', type=int, default=100)
        self.reqparse.add_argument('subsystems', type=str, default=None, action='append')

        args = self.reqparse.parse_args()
        total_qry = db.query(func.count(Email.email_id))
        qry = db.Email.order_by(desc(Email.timestamp))

        if args['subsystems']:
            authsystems = [x for x in map(lambda x: x.lower(), args['subsystems'])]
            qry = qry.filter(func.lower(Email.subsystem).in_(authsystems))
            total_qry = total_qry.filter(func.lower(Email.subsystem).in_(authsystems))

        if (args['page'] - 1) > 0:
            offset = (args['page'] - 1) * args['count']
            qry = qry.offset(offset)

        qry = qry.limit(args['count'])
        emails = qry.all()
        total_emails = total_qry.first()[0]

        return self.make_response({
            'message': None,
            'emailCount': total_emails,
            'emails': emails,
            'subsystems': [x[0] for x in db.query(distinct(Email.subsystem)).all()]
        })


class EmailGet(BaseView):
    URLS = ['/api/v1/emails/<int:emailId>']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self, emailId):
        email = db.Email.find_one(Email.email_id == emailId)

        if not email:
            return self.make_response({
                'message': 'Email not found',
                'email': None
            }, HTTP.NOT_FOUND)

        return self.make_response({
            'email': email.to_json(True)
        })

    @rollback
    @check_auth(ROLE_ADMIN)
    def put(self, emailId):
        email = db.Email.find_one(Email.email_id == emailId)
        if not email:
            return self.make_response({
                'message': 'Email not found',
                'email': None
            }, HTTP.NOT_FOUND)

        try:
            send_notification(
                subsystem=email.subsystem,
                recipients=[NotificationContact('email', x) for x in email.recipients],
                subject=email.subject,
                body_html=email.message_html,
                body_text=email.message_text
            )

            auditlog(event='email.resend', actor=session['user'].username, data={'emailId': emailId})
            return self.make_response('Email resent successfully')

        except EmailSendError as ex:
            self.log.exception('Failed resending email {0}: {1}'.format(email.email_id, ex))
            return self.make_response('Failed resending the email: {0}'.format(ex), HTTP.UNAVAILABLE)
