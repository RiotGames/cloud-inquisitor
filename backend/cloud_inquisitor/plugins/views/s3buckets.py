from cloud_inquisitor.constants import ROLE_USER
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.wrappers import check_auth, rollback


class S3BucketList(BaseView):
    URLS = ['/api/v1/domainhijacking']

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('page', type=int, default=None)
        self.reqparse.add_argument('fixed', type=str, default=False)
        self.reqparse.add_argument('count', type=int, default=25)
        self.reqparse.add_argument('account', type=str, default=None)
        args = self.reqparse.parse_args()

        self.log.info(args)
