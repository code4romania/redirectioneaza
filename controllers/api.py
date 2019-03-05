from logging import info
from flask import abort, render_template, url_for, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
from hashlib import sha1, md5
from sqlalchemy import func
from models.models import NgoEntity
from models.handlers import BaseHandler
from appengine_config import USER_UPLOADS_FOLDER, DEFAULT_NGO_LOGO

# from models.storage import CloudStorage
# from models.create_pdf import create_pdf
# from webapp2_extras import json, security
# from google.appengine.ext.ndb import Key
# from google.appengine.api import users, urlfetch


# TODO RENAME NGO_ID TO NGO_URL
def check_ngo_url(ngo_id=None):
    if not ngo_id: 
        return False

    return NgoEntity.query.filter_by(url=ngo_id).first() is None

class CheckNgoUrl(BaseHandler):

    def get(self, ngo_url):

        # if we don't receive an ngo url or it's not a logged in user or not and admin
        #TODO Find out where we checked for both authenticated user and admin
        if not ngo_url or not current_user.is_authenticated:
            return abort(403)

        if check_ngo_url(ngo_url):
            return "",200
        else:
            return "",400

class NgosApi(BaseHandler):

    def get(self):

        # get all the visible ngos
        ngos = NgoEntity.query.filter_by(active=True).all()

        response = []
        for ngo in ngos:
            response.append({
                "name": ngo.name,
                "url": url_for('twopercent', ngo_url=ngo.url),
                "logo": ngo.logo if ngo.logo else DEFAULT_NGO_LOGO
            })

        #self.return_json(response)
        return jsonify(response)

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

class GetUploadUrl(BaseHandler):

    @login_required
    def post(self):

        files = request.files

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

            if not current_user.is_admin:
                folder = str(self.user.email)
            else:
                folder = "admin"

            # the user's folder name, it's just his md5 hashed db id
            user_folder = hashlib.md5(folder) 

            # a way to create unique file names
            # get the local time in iso format
            # run that through SHA1 hash
            # output a hex string
            filename = "{0}/{1}/{2}".format(USER_UPLOADS_FOLDER, str(user_folder), sha1( datetime.now().isoformat() ).hexdigest())
        
            #TODO Rewrite this with non GAE Logic
            #file_url = CloudStorage.save_file(a_file, filename)
            
            if file_url:
                file_urls.append( file_url )


        return jsonify({
            "file_urls": file_urls
        })
