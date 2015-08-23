

from google.appengine.ext.ndb import Key
from google.appengine.api import users

from models.models import NgoEntity
from models.handlers import AccountHandler



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
            self.response.set_status(404)

