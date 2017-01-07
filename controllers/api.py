
from datetime import datetime
from hashlib import sha1

from google.appengine.ext.ndb import Key
from google.appengine.api import users, urlfetch

from models.models import NgoEntity
from models.handlers import AccountHandler, user_required
from models.storage import CloudStorage

from appengine_config import USER_UPLOADS_FOLDER

from webapp2_extras import json, security

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

    @user_required
    def post(self):

        post = self.request

        # we must use post.POST so we get a file instante
        files = post.POST.getall("files")

        if len(files) == 0:
            self.abort(400)

        file_urls = []
        for a_file in files:

            # jump over files that are not images
            # https://docs.python.org/2/library/imghdr.html
            # if imghdr.what("", h=a_file.file.read()) is None
            if not a_file.type or a_file.type.split("/")[0] != "image":
                continue

            info(a_file.type)

            # if the image is uploaded by the admin
            # we don't have an user
            if self.user:
                folder = str(self.user.key.id())
            else:
                folder = "admin"

            # the user's folder name, it's just his md5 hashed db id
            user_folder = security.hash_password(folder, "md5")

            # a way to create unique file names
            # get the local time in iso format
            # run that through SHA1 hash
            # output a hex string
            filename = "{0}/{1}/{2}".format(USER_UPLOADS_FOLDER, str(user_folder), sha1( datetime.now().isoformat() ).hexdigest())
        
            file_url = CloudStorage.save_file(a_file, filename)
            
            if file_url:
                file_urls.append( file_url )


        self.return_json({
            "file_urls": file_urls
        })
