

from google.appengine.ext.ndb import Key
from google.appengine.api import users, urlfetch

from models.models import NgoEntity
from models.handlers import AccountHandler
from models.upload import UploadHandler

import json
from logging import info


def check_ngo_url(ngo_id=None):
    if not ngo_id: 
        return False

    return NgoEntity.query(NgoEntity.key == Key("NgoEntity", ngo_id)).count(limit=1) == 0


class CheckNgoUrl(AccountHandler):

    def get(self, ngo_url):

        # if we don't receive an ngo url or it's not a logged in user or not and admin
        if not ngo_url or not self.user_info and not users.is_current_user_admin():
            self.abort(403)

        if check_ngo_url(ngo_url):
            self.response.set_status(200)
        else:
            self.response.set_status(400)

class GetUploadUrl(AccountHandler):

    def get(self):

        file_name = self.request.get("file_name")
        file_type = self.request.get("file_type")

        if not file_type or not file_type:
            self.set_status(400)

        response = UploadHandler.get_signed_url(file_name, file_type)

        if response is not False:
            self.response.write(json.dumps(response))
        else:
            self.set_status(400)

