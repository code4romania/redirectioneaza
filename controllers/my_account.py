

from google.appengine.ext.ndb import put_multi, OR, Key
from google.appengine.api import users

from appengine_config import AWS_PDF_URL, LIST_OF_COUNTIES

from models.handlers import AccountHandler, user_required
from models.models import NgoEntity, Donor
from models.upload import UploadHandler

from api import check_ngo_url

incomplete_form_data = "Te rugam sa completezi datele din formular."
url_taken = "Din pacate acest url este folosit deja."

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
            # self.uri_for("ngo-url", ngo_url=ngo.key.id(), _full=True)

            donors = Donor.query(Donor.ngo == ngo.key).fetch()
            self.template_values["donors"] = donors

        else:
            self.template_values["ngo"] = {}
    
            self.template_values["counties"] = LIST_OF_COUNTIES

            # self.uri_for("api-ngo-check-url", ngo_url="")
            # TODO: use uri_for
            self.template_values["check_ngo_url"] = "/api/ngo/check-url/"
            
            self.template_values["ngo_upload_url"] = self.uri_for("api-ngo-upload-url")

        
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
        self.template_values["title"] = "Date cont"

        first_name = self.request.get('nume')
        last_name = self.request.get('prenume')

        if not first_name or not last_name:
            self.template_values["errors"] = incomplete_form_data
            self.render()
            return

        user.first_name = first_name
        user.last_name = last_name
        # user.email = email

        user.put()

        self.render()

class NgoDetailsHandler(AccountHandler):
    template_name = 'ngo/ngo-details.html'
    @user_required
    def get(self):
        user = self.user
        self.template_values["title"] = "Date asociatie"

        # if the user has an ngo attached, allow him to edit it
        if user.ngo:
            self.template_values["user"] = user
            
            ngo = user.ngo.get()
            self.template_values["ngo"] = ngo
            self.template_values["ngo_upload_url"] = self.uri_for("api-ngo-upload-url")
            self.template_values["counties"] = LIST_OF_COUNTIES
            
            self.render()
        else:
            # if not redirect to home
            self.template_values["ngo"] = {}
            self.redirect(self.uri_for("contul-meu"))
            
    def post(self):
        
        user = self.user
        if user is None:
            if users.is_current_user_admin():
                user = users.get_current_user()
                user.ngo = Key(NgoEntity, self.request.get('ong-url'))
            else:
                self.abort(403)

        self.template_values["user"] = user


        ong_nume = self.request.get('ong-nume')

        ong_logo_url = self.request.get('ong-logo-url')
        # this file should be received only if js is disabled
        ong_logo = self.request.get('ong-logo') if ong_logo_url is None else None
        
        ong_descriere = self.request.get('ong-descriere')
        
        ong_tel = self.request.get('ong-tel', "")
        ong_email = self.request.get('ong-email', "")
        ong_website = self.request.get('ong-website', "")

        ong_adresa = self.request.get('ong-adresa')
        ong_judet = self.request.get('ong-judet', "")

        ong_cif = self.request.get('ong-cif')
        ong_account = self.request.get('ong-cont')

        ong_url = self.request.get('ong-url')
        
        # validation
        if not ong_nume or not ong_descriere or not ong_adresa or not ong_url or not ong_cif or not ong_account:
            self.template_values["errors"] = incomplete_form_data
            self.render()
            return

        # TODO: in the future
        # try:
        #     # try and cut it ad 1400 bytes, if we have an error
        #     short_description = utf8_byte_truncate(ong_descriere, 1400)
        # except Exception, e:
        #     # cut it at 80 chars
        #     short_description = ong_descriere[:180]
        
        # cut the short description at 180
        short_description = ong_descriere[:180]

        # if the user already has an ngo, update it
        if user.ngo:

            ngo = user.ngo.get()
            # if the user has an ngo attached but it's not found, create a new one
            if ngo is not None:

                ngo.name = ong_nume
                ngo.description = ong_descriere
                ngo.short_description = short_description
                ngo.logo = ong_logo_url

                ngo.address = ong_adresa
                ngo.county = ong_judet

                ngo.email = ong_email
                ngo.website = ong_website
                ngo.tel = ong_tel
                
                # if no one uses this CIF
                if ong_cif != ngo.cif:
                    cif_unique = NgoEntity.query(NgoEntity.cif == ong_cif).count(limit=1) == 0
                    if cif_unique:
                        ngo.cif = ong_cif
                    else:
                        self.template_values["unique"] = False
                        self.render()
                        return

                # and no one uses this bank account
                if ong_account != ngo.account:
                    acc_unique = NgoEntity.query(NgoEntity.account == ong_account).count(limit=1) == 0
                    if acc_unique:
                        ngo.account = ong_account
                    else:
                        self.template_values["unique"] = False
                        self.render()
                        return

                if users.is_current_user_admin():
                    ngo.verified = self.request.get('ong-verificat', "off") == "on"
                    ngo.active = self.request.get('ong-activ', "on") == "on"

                # save the changes
                ngo.put()
                
                if users.is_current_user_admin():
                    self.redirect(self.uri_for("admin-ong", ngo_url=ong_url))
                else:
                    self.redirect(self.uri_for("asociatia"))
    
                return

        # check for unique url
        is_ngo_url_avaible = check_ngo_url(ong_url)
        if is_ngo_url_avaible == False:
            self.template_values["errors"] = url_taken
            self.render()
            return

        unique = NgoEntity.query(OR(NgoEntity.cif == ong_cif, NgoEntity.account == ong_account)).count(limit=1) == 0
        if not unique:
            # asks if he represents the ngo

            self.template_values["unique"] = False
            self.render()
            return
        else:
            self.template_values["unique"] = True

        if ong_logo_url is None and ong_logo is not None:
            # upload file to S3 if received else None
            ong_logo_url = UploadHandler.upload_file_to_s3(ong_logo, ong_url) if ong_logo else None
        

        # create a new ngo entity
        new_ngo = NgoEntity(
            id = ong_url,

            name = ong_nume,
            description = ong_descriere,
            short_description = short_description,
            logo = ong_logo_url,
            
            email = ong_email,
            website = ong_website,
            tel = ong_tel,
            
            address = ong_adresa,
            county = ong_judet,
            
            cif = ong_cif,
            account = ong_account
        )

        if users.is_current_user_admin():

            # a list of email addresses
            new_ngo.other_emails = [s.strip() for s in self.request.get('alte-adrese-email', "").split(",")]

            new_ngo.put()
        
            self.redirect(self.uri_for("admin-ong", ngo_url=ong_url))
        else:
            # link this user with the ngo
            # the ngo has a key even though we haven't saved it, we offered it an unique id
            user.ngo = new_ngo.key
            
            # use put_multi to save rpc calls
            put_multi([new_ngo, user])

            # do a refresh
            self.redirect(self.uri_for("contul-meu"))

    def utf8_byte_truncate(text, max_bytes):
        """ truncate utf-8 text string to no more than max_bytes long """
        byte_len = 0
        _incr_encoder.reset()
        for index,ch in enumerate(text):
            byte_len += len(_incr_encoder.encode(ch))
            if byte_len > max_bytes:
                break
        else:
            return text
        
        result = text[:index]

        return result