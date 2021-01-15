
import datetime

from collections import OrderedDict

from google.appengine.ext.ndb import put_multi, OR, Key
from google.appengine.api import users
from google.appengine.api import mail

from appengine_config import LIST_OF_COUNTIES, CONTACT_EMAIL_ADDRESS, START_YEAR, DONATION_LIMIT

from models.handlers import AccountHandler, user_required
from models.models import NgoEntity, Donor
from models.user import User

from api import check_ngo_url
from logging import info


incomplete_form_data = "Te rugam sa completezi datele din formular."
url_taken = "Din pacate acest url este folosit deja."
not_unique = 'Se pare ca acest cod CIF sau cont bancar este deja inscris. ' \
             'Daca reprezinti ONG-ul cu aceste date, te rugam sa ne contactezi.'

class MyAccountHandler(AccountHandler):
    template_name = 'ngo/my-account.html'

    @user_required
    def get(self):

        user = self.user
        self.template_values["user"] = user
        self.template_values["title"] = "Contul meu"
        self.template_values['limit'] = DONATION_LIMIT

        now = datetime.datetime.now()

        if user.ngo:
            ngo = user.ngo.get()
            self.template_values["ngo"] = ngo

            # the url to distribute, use this instead of:
            # self.uri_for("ngo-url", ngo_url=ngo.key.id(), _full=True)
            self.template_values["ngo_url"] = self.request.host + '/' + ngo.key.id() 

            donor_projection = ['first_name', 'last_name', 'city', 'county', 'email', 'tel', 'anonymous', 'date_created']
            donors = Donor.query(Donor.ngo == ngo.key).order(-Donor.date_created).fetch(projection=donor_projection)
            
            years = xrange(now.year, START_YEAR-1, -1)
            grouped_donors = OrderedDict()
            for year in years:
                grouped_donors[year] = []
            

            # group the donors by year
            for donor in donors:

                index = donor.date_created.year
                
                if index in years:
                    grouped_donors[ index ].append(donor)

            self.template_values["current_year"] = now.year
            self.template_values["donors"] = grouped_donors
            # self.template_values["years"] = years
            
            can_donate = not now.date() > DONATION_LIMIT

            self.template_values["can_donate"] = can_donate

        else:
            self.template_values["ngo"] = {}
    
            self.template_values["counties"] = LIST_OF_COUNTIES

            # self.uri_for("api-ngo-check-url", ngo_url="")
            # TODO: use uri_for
            # self.template_values["check_ngo_url"] = "/api/ngo/check-url/"
            
            # self.template_values["ngo_upload_url"] = self.uri_for("api-ngo-upload-url")

        
        self.render()

class MyAccountDetailsHandler(AccountHandler):
    template_name = 'ngo/my-account-details.html'

    @user_required
    def get(self):

        user = self.user
        self.template_values["user"] = user
        self.template_values["title"] = "Date cont"
        
        self.render()
    
    @user_required
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
            self.template_values["counties"] = LIST_OF_COUNTIES
            
            self.render()
        else:
            # if not redirect to home
            self.template_values["ngo"] = {}
            self.redirect(self.uri_for("contul-meu"))
            
    @user_required
    def post(self):
        
        user = self.user
        if user is None:
            if users.is_current_user_admin():
                user = users.get_current_user()

                old_ngo_key = self.request.get('old-ong-url') if self.request.get('old-ong-url') else 1

                user.ngo = Key(NgoEntity, old_ngo_key)
            else:
                self.abort(403)

        self.template_values["user"] = user
        self.template_values["ngo"] = {}
        self.template_values["counties"] = LIST_OF_COUNTIES
        # self.template_values["check_ngo_url"] = "/api/ngo/check-url/"
        # self.template_values["ngo_upload_url"] = self.uri_for("api-ngo-upload-url")


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
        ong_activity = self.request.get('ong-activitate', "")

        ong_cif = self.request.get('ong-cif')
        ong_account = self.request.get('ong-cont')
        ong_special_status = self.request.get('special-status') == "on"

        ong_url = self.request.get('ong-url')

        # validation
        if not ong_nume or not ong_descriere or not ong_adresa or not ong_url or not ong_cif or not ong_account:
            self.template_values["errors"] = incomplete_form_data
            self.render()
            return

        # remove white spaces from account
        ong_account = ong_account.replace(' ', '')

        # if the user already has an ngo, update it
        if user.ngo:

            ngo = user.ngo.get()

            # if the user has an ngo attached but it's not found, skip this and create a new one
            if ngo is not None:

                # if the name, cif or bank account changed, remove the form url so we create it again
                if ong_nume != ngo.name or ong_cif != ngo.cif or ong_account != ngo.account:
                    # if we encounter validation errors later, this will not get saved
                    # so it's safe to do it here
                    ngo.form_url = None

                ngo.name = ong_nume
                ngo.description = ong_descriere
                ngo.logo = ong_logo_url

                ngo.address = ong_adresa
                ngo.county = ong_judet
                ngo.active_region = ong_activity

                ngo.email = ong_email
                ngo.website = ong_website
                ngo.tel = ong_tel

                ngo.special_status = ong_special_status

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
                    ngo.verified = self.request.get('ong-verificat') == "on"
                    ngo.active = self.request.get('ong-activ') == "on"

                    # if we want to change the url
                    if ong_url != ngo.key.id():

                        is_ngo_url_available = check_ngo_url(ong_url)
                        if is_ngo_url_available == False:
                            self.template_values["errors"] = url_taken
                            self.render()
                            return
                        
                        new_key = Key(NgoEntity, ong_url)

                        # replace all the donors key
                        donors = Donor.query(Donor.ngo == ngo.key).fetch()
                        if donors:
                            for donor in donors:
                                donor.ngo = new_key 
                                donor.put()

                        # replace the users key
                        ngos_user = User.query(Donor.ngo == ngo.key).get()
                        if ngos_user:
                            ngos_user.ngo = new_key
                            ngos_user.put()

                        # copy the old model
                        new_ngo = ngo
                        # delete the old model
                        ngo.key.delete()
                        # add a new key
                        new_ngo.key = new_key
                        
                        ngo = new_ngo


                # save the changes
                ngo.put()
                
                if users.is_current_user_admin():
                    self.redirect(self.uri_for("admin-ong", ngo_url=ong_url))
                else:
                    self.redirect(self.uri_for("asociatia"))

                return

        # create a new ngo entity
        # do this before validating the url, cif and back account because if we have errors 
        # to at least prepopulate the form on refresh
        new_ngo = NgoEntity(
            id = ong_url,

            name = ong_nume,
            description = ong_descriere,
            logo = ong_logo_url,
            
            email = ong_email,
            website = ong_website,
            tel = ong_tel,
            
            address = ong_adresa,
            county = ong_judet,
            
            cif = ong_cif,
            account = ong_account,
            special_status = ong_special_status
        )

        # check for unique url
        is_ngo_url_available = check_ngo_url(ong_url)
        if is_ngo_url_available == False:
            self.template_values["errors"] = url_taken

            new_ngo.key = None
            self.template_values["ngo"] = new_ngo
            
            self.render()
            return


        unique = NgoEntity.query(OR(NgoEntity.cif == ong_cif, NgoEntity.account == ong_account)).count(limit=1) == 0
        if not unique:
            # asks if he represents the ngo

            self.template_values["errors"] = not_unique
            self.render()
            return
        else:
            self.template_values["errors"] = True

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

            # try:
            #     subject = "O noua organizatie s-a inregistrat"
            #     values = {
            #         "ngo": ong_nume,
            #         "link": self.request.host + '/' + new_ngo.key.id()
            #     }
            #     body = self.jinja_enviroment.get_template("email/admin/new-ngo.txt").render(values)
            #     # info(body)
            #     mail.send_mail(sender=CONTACT_EMAIL_ADDRESS, to="donezsieu@gmail.com", subject=subject, body=body)
            # except Exception, e:
            #     info(e)

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