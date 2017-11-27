from flask import current_app

from cloud_inquisitor.plugins import BaseView


class LoginRedirectView(BaseView):
    def get(self):
        authsys = current_app.active_auth_system
        return self.make_response(authsys.login)


class LogoutRedirectView(BaseView):
    def get(self):
        authsys = current_app.active_auth_system
        return self.make_response({'url': authsys.logout})
