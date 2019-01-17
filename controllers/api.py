
from datetime import datetime
from hashlib import sha1

from google.appengine.ext.ndb import Key
from google.appengine.api import users, urlfetch

from models.models import NgoEntity
from models.handlers import BaseHandler, AccountHandler, user_required
from models.storage import CloudStorage
from models.create_pdf import create_pdf

from appengine_config import USER_UPLOADS_FOLDER, DEFAULT_NGO_LOGO

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

class NgosApi(BaseHandler):

    def get(self):

        # get all the visible ngos
        ngos = NgoEntity.query(NgoEntity.active == True).fetch()

        response = []
        for ngo in ngos:
            response.append({
                "name": ngo.name,
                "url": self.uri_for('twopercent', ngo_url=ngo.key.id()),
                "logo": ngo.logo if ngo.logo else DEFAULT_NGO_LOGO
            })

        self.return_json(response)

class GetNgoForm(BaseHandler):

    def get(self, ngo_url):
        
        ngo = NgoEntity.get_by_id(ngo_url)

        if not ngo:
            self.abort(404)

        # if we have an form created for this ngo, return the url
        # if ngo.form_url:
        #     self.redirect( str(ngo.form_url), abort=True )

        # else, create a new one and upload to GCS for future use
        ngo_dict = {
            "name": ngo.name,
            "cif": ngo.cif,
            "account": ngo.account,
            "special_status": ngo.special_status
        }
        pdf = create_pdf({}, ngo_dict)

        # filename = "Formular 2% - {0}.pdf".format(ngo.name)
        filename = "Formular_donatie.pdf".format(ngo.name)
        ong_folder = security.hash_password(ngo.key.id(), "md5")
        path = "{0}/{1}/{2}".format(USER_UPLOADS_FOLDER, str(ong_folder), filename)

        file_url = CloudStorage.save_file(pdf, path)

        # close the file after it has been uploaded
        pdf.close()

        ngo.form_url = file_url
        ngo.put()

        self.redirect(str(ngo.form_url))

class GetUploadUrl(AccountHandler):

    @user_required
    def post(self):

        post = self.request

        # we must use post.POST so we get the file
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
