import os
from datetime import datetime
from hashlib import sha1, md5
from logging import info

from flask import abort, url_for, jsonify, request, redirect
from flask_login import current_user, login_required

from config import DEFAULT_NGO_LOGO
from core import db, app
from models.create_pdf import create_pdf
from models.handlers import BaseHandler
from models.models import NgoEntity


def check_ngo_url(ngo_url=None):
    if not ngo_url:
        return False

    return NgoEntity.query.filter_by(url=ngo_url).first() is None


class CheckNgoUrl(BaseHandler):

    def get(self, ngo_url):

        # if we don't receive an ngo url or it's not a logged in user or not and admin
        # TODO Find out where we checked for both authenticated user and admin
        if not ngo_url or not current_user.is_authenticated:
            return abort(403)

        if check_ngo_url(ngo_url):
            return "", 200
        else:
            return "", 400


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
        return jsonify(response)


class GetNgoForm(BaseHandler):

    def get(self, ngo_url):
        _ngo = NgoEntity.query.filter_by(url=ngo_url).first()

        if not _ngo:
            return abort(404)

        # TODO implement check if form already exists, serve it

        # if we have an form created for this ngo, return the url
        if _ngo.form_url:
            return redirect(str(_ngo.form_url), abort=True)

        ngo_dict = {
            "name": _ngo.name,
            "cif": _ngo.cif,
            "account": _ngo.account,
            "special_status": _ngo.special_status
        }
        pdf = create_pdf({}, ngo_dict)

        # filename = "Formular 2% - {0}.pdf".format(ngo.name)
        # filename = "Formular_donatie.pdf".format(_ngo.name)
        #
        # # TODO Is this really a good idea - hashing an ID that can change?
        # ong_folder = security.hash_password(_ngo.url, "md5")
        #
        # path = "{0}/{1}/{2}".format(USER_UPLOADS_FOLDER, str(ong_folder), filename)

        _ngo.form_url = pdf
        db.session.merge(_ngo)
        db.session.commit()

        return redirect(str(_ngo.form_url))


class GetUploadUrl(BaseHandler):

    @login_required
    def post(self):
        # TODO Rewrite this using S3

        files = request.files

        if len(files) == 0:
            return abort(400)

        file_urls = []
        for uploaded_file in files.values():

            if not uploaded_file.mimetype or uploaded_file.mimetype.split("/")[0] != "image":
                continue

            info(uploaded_file.mimetype)

            if not current_user.is_admin:
                folder = str(current_user.email)
            else:
                folder = "admin"

            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(md5(folder.encode('utf-8')).hexdigest()))

            filename = sha1(datetime.now().isoformat().encode('utf-8')).hexdigest() + '.' \
                       + uploaded_file.mimetype.split('/')[1]

            file_url = os.path.join(user_folder, filename)

            if not os.path.isdir(user_folder):
                os.mkdir(user_folder)

            uploaded_file.save(file_url)

            if file_url:
                file_urls.append(file_url)

        return jsonify({
            "file_urls": file_urls
        })
