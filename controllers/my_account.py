

from google.appengine.ext.ndb import Key, put_multi

from appengine_config import AWS_PDF_URL

from models.handlers import AccountHandler, user_required
from models.models import NgoEntity, Donor
from models.upload import UploadHandler

from logging import info

def check_ngo_url(ngo_id=None):
    if not ngo_id: 
        return False

    return NgoEntity.query(NgoEntity.key == Key("NgoEntity", ngo_id)).count(1) == 0

class MyAccountHandler(AccountHandler):
    template_name = 'ngo/my-account.html'

    @user_required
    def get(self):

        user = self.user
        self.template_values["user"] = user

        if user.ngo:
            ngo = user.ngo.get()
            self.template_values["ngo"] = ngo
            # to url to distribute
            self.template_values["ngo_url"] = self.request.host + '/' + ngo.key.id()

            donors = Donor.query(Donor.ngo == ngo.key).fetch()
            self.template_values["donors"] = donors

        else:
            self.template_values["AWS_SERVER_URL"] = AWS_PDF_URL + "/upload-file"
        
        self.render()

    def post(self):
        
        user = self.user
        if user is None:
            self.abort(403)

        self.template_values["user"] = user

        ong_nume = self.request.get('ong-nume')
        ong_logo_url = self.request.get('ong-logo-url')
        # this file should be received only if the
        ong_logo = self.request.get('ong-logo') if ong_logo_url is None else None
        
        ong_descriere = self.request.get('ong-descriere')
        ong_adresa = self.request.get('ong-adresa')

        ong_cif = self.request.get('ong-cif')
        ong_account = self.request.get('ong-cont')

        
        ong_url = self.request.get('ong-url')
        
        if not ong_nume or not ong_descriere or not ong_adresa or not ong_url or not ong_cif or not ong_account:
            self.template_values["errors"] = "Te rugam sa completezi datele din formular."
            self.render()
            return

        is_ngo_url_avaible = check_ngo_url(ong_url)

        if is_ngo_url_avaible == False:
            self.template_values["errors"] = "Din pacate acest url este folosit deja."
            self.render()
            return

        if ong_logo_url is None and ong_logo is not None:
            # upload file to S3 if received else None
            ong_logo_url = UploadHandler.upload_file_to_s3(ong_logo, ong_url) if ong_logo else None

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



class NgoDetailsHandler(AccountHandler):
    template_name = 'ngo/ngo-details.html'
    @user_required
    def get(self):
        user = self.user

        if user.ngo:
            self.template_values["user"] = user
            
            ngo = user.ngo.get()
            self.template_values["ngo"] = ngo
            
            self.render()
        else:
            self.redirect(self.uri_for("contul-meu"))
            


class NgoDonationsHandler(AccountHandler):
    @user_required
    def get(self):
        self.redirect(self.uri_for("donatii-doilasuta"))

class NgoTwoPercentHandler(AccountHandler):
    template_name = 'ngo/twopercent.html'

    @user_required
    def get(self):
        user = self.user

        if user.ngo:
            ngo = user.ngo.get()
        else:
            self.redirect(self.uri_for("contul-meu"))
            return

        self.template_values["user"] = user
        self.template_values["ngo"] = ngo

        self.render()

    def post(self):
        user = self.user
        if user is None:
            self.abort(403)

        if user.ngo:
            ngo = user.ngo.get()
        else:
            self.abort(400)

        ngo_cif = self.request.get('ong-cif')
        ngo_account = self.request.get('ong-cont')

        if not ngo_cif or not ngo_account:
            self.template_values["errors"] = "Va rugam completati codul CIF si contul bancar al asociatiei."
            self.render()

        ngo.cif = ngo_cif
        ngo.account = ngo_account

        ngo.put()

        self.redirect(self.uri_for("donatii-doilasuta"))
        