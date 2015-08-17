

from google.appengine.ext.ndb import Key, put_multi

from appengine_config import AWS_PDF_URL

from models.handlers import AccountHandler, user_required
from models.models import NgoEntity, Donor
from models.upload import UploadHandler

from api import check_ngo_url

from logging import info

class MyAccountHandler(AccountHandler):
    template_name = 'ngo/my-account.html'

    @user_required
    def get(self):

        user = self.user
        self.template_values["user"] = user
        self.template_values["title"] = "Contul meu"

        if user.ngo:
            ngo = user.ngo.get()
            self.template_values["ngo"] = ngo
            # to url to distribute
            self.template_values["ngo_url"] = self.request.host + '/' + ngo.key.id()

            donors = Donor.query(Donor.ngo == ngo.key).fetch()
            self.template_values["donors"] = donors

        else:
            self.template_values["ngo"] = {}
            self.template_values["AWS_SERVER_URL"] = AWS_PDF_URL + "/upload-file"
            self.template_values["check_ngo_url"] = "/api/check-ngo-api/"

        
        self.render()

class MyAccountDetailsHandler(AccountHandler):
    template_name = 'ngo/my-account-details.html'

    @user_required
    def get(self):

        user = self.user
        self.template_values["user"] = user
        self.template_values["title"] = "Date cont"
        
        self.render()
    def post(self):
        
        user = self.user
        if user is None:
            self.abort(403)

        self.template_values["user"] = user

        first_name = self.request.get('nume')
        last_name = self.request.get('prenume')

        email = self.request.get('email')

        if not first_name or not last_name or not email:
            self.template_values["errors"] = "Te rugam sa completezi datele din formular."
            self.render()
            return

        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        user.put()

        self.render()

class NgoDetailsHandler(AccountHandler):
    template_name = 'ngo/ngo-details.html'
    @user_required
    def get(self):
        user = self.user
        self.template_values["title"] = "Date asociatie"

        if user.ngo:
            self.template_values["user"] = user
            
            ngo = user.ngo.get()
            self.template_values["ngo"] = ngo
            self.template_values["AWS_SERVER_URL"] = AWS_PDF_URL + "/upload-file"
            
            self.render()
        else:
            self.template_values["ngo"] = {}
            self.redirect(self.uri_for("contul-meu"))
            
    def post(self):
        
        user = self.user
        if user is None:
            self.abort(403)

        self.template_values["user"] = user


        ong_nume = self.request.get('ong-nume')
        ong_logo_url = self.request.get('ong-logo-url')

        # this file should be received only if js is disabled
        ong_logo = self.request.get('ong-logo') if ong_logo_url is None else None
        
        ong_descriere = self.request.get('ong-descriere')
        ong_adresa = self.request.get('ong-adresa')

        ong_cif = self.request.get('ong-cif')
        ong_account = self.request.get('ong-cont')

        ong_url = self.request.get('ong-url')
        
        # validation
        if not ong_nume or not ong_descriere or not ong_adresa or not ong_url or not ong_cif or not ong_account:
            self.template_values["errors"] = "Te rugam sa completezi datele din formular."
            self.render()
            return

        # if the user already has an ngo, update it
        if user.ngo:
            ngo = user.ngo.get()

            ngo.name = ong_nume
            ngo.description = ong_descriere
            ngo.logo = ong_logo_url
            ngo.address = ong_adresa
            ngo.cif = ong_cif
            ngo.account = ong_account
            # save the changes
            ngo.put()

            self.redirect(self.uri_for("asociatia"))
        else:
            # check for unique url
            is_ngo_url_avaible = check_ngo_url(ong_url)
            if is_ngo_url_avaible == False:
                self.template_values["errors"] = "Din pacate acest url este folosit deja."
                self.render()
                return

            if ong_logo_url is None and ong_logo is not None:
                # upload file to S3 if received else None
                ong_logo_url = UploadHandler.upload_file_to_s3(ong_logo, ong_url) if ong_logo else None
            
            # create a new ngo entity
            new_ngo = NgoEntity(
                id = ong_url,
                name = ong_nume,
                description = ong_descriere,
                logo = ong_logo_url,
                address = ong_adresa,
                cif = ong_cif,
                account = ong_account
            )

            # link this user with the ngo
            # the ngo has a key even though we haven't saved it, we offered it an unique id
            user.ngo = new_ngo.key
            
            # use put_multi to save rpc calls
            put_multi([new_ngo, user])

            # do a refresh
            self.redirect(self.uri_for("contul-meu"))