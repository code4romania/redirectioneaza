import datetime
from collections import OrderedDict

from flask import render_template, url_for, request, redirect
from flask_login import login_required, current_user

from redirectioneaza import db
from redirectioneaza.config import START_YEAR
from redirectioneaza.contact_data import LIST_OF_COUNTIES
from redirectioneaza.handlers.base import BaseHandler
from redirectioneaza.models import NgoEntity, Donor
from .api import check_ngo_url

incomplete_form_data = "Te rugam sa completezi datele din formular."
url_taken = "Din pacate acest url este folosit deja."
not_unique = 'Se pare ca acest cod CIF sau cont bancar este deja inscris. ' \
             'Daca reprezinti ONG-ul cu aceste date, te rugam sa ne contactezi.'


class MyAccountHandler(BaseHandler):
    template_name = 'ngo/my-account.html'

    @login_required
    def get(self):

        user = current_user  # User.query.get(1)
        self.template_values["user"] = user
        self.template_values["title"] = "Contul meu"

        now = datetime.datetime.now()

        if user.ngo:
            self.template_values["ngo"] = user.ngo

            self.template_values["ngo_url"] = url_for('asociatia') + '/' + str(user.ngo.url)

            donors = Donor.query.with_entities(Donor.first_name,
                                               Donor.last_name,
                                               Donor.city,
                                               Donor.county,
                                               Donor.email,
                                               Donor.tel,
                                               Donor.anonymous,
                                               Donor.date_created).filter_by(ngo=user.ngo) \
                .order_by(Donor.date_created.desc()) \
                .all()
            years = range(now.year, START_YEAR - 1, -1)
            grouped_donors = OrderedDict()
            for year in years:
                grouped_donors[year] = []

            # group the donors by year
            for donor in donors:

                index = donor.date_created.year

                if index in years:
                    grouped_donors[index].append(donor)

            self.template_values["current_year"] = now.year
            self.template_values["donors"] = grouped_donors

            can_donate = True
            if now.month > 5 or now.month == 5 and now.day > 25:
                can_donate = False

            self.template_values["can_donate"] = can_donate

        else:
            self.template_values["ngo"] = {}

            self.template_values["counties"] = LIST_OF_COUNTIES

            # self.uri_for("api-ngo-check-url", ngo_url="")
            # self.template_values["check_ngo_url"] = "/api/ngo/check-url/"

            # self.template_values["ngo_upload_url"] = self.uri_for("api-ngo-upload-url")

        return render_template(self.template_name, **self.template_values)


class MyAccountDetailsHandler(BaseHandler):
    template_name = 'ngo/my-account-details.html'

    @login_required
    def get(self):
        user = current_user
        self.template_values["user"] = user
        self.template_values["title"] = "Date cont"

        return render_template(self.template_name, **self.template_values)

    @login_required
    def post(self):
        user = current_user
        # if user is None:
        #     self.abort(403)

        self.template_values["user"] = user
        self.template_values["title"] = "Date cont"

        first_name = request.form.get('nume')
        last_name = request.form.get('prenume')

        if not first_name or not last_name:
            self.template_values["errors"] = incomplete_form_data
            return render_template(self.template_name, **self.template_values)

        user.first_name = first_name
        user.last_name = last_name

        db.session.merge(user)

        db.session.commit()

        return render_template(self.template_name, **self.template_values)


class NgoDetailsHandler(BaseHandler):
    template_name = 'ngo/ngo-details.html'

    @login_required
    def get(self):
        user = current_user
        self.template_values["title"] = "Date asociatie"

        # if the user has an ngo attached, allow him to edit it
        if user.ngo:
            self.template_values["user"] = user

            self.template_values["ngo"] = user.ngo
            # self.template_values["ngo_upload_url"] = self.uri_for("api-ngo-upload-url")
            self.template_values["counties"] = LIST_OF_COUNTIES

            return render_template(self.template_name, **self.template_values)
        else:
            # if not redirect to home
            self.template_values["ngo"] = {}
            return redirect(url_for("contul-meu"))

    @login_required
    def post(self):

        user = current_user

        self.template_values["user"] = user
        self.template_values["ngo"] = {}
        self.template_values["counties"] = LIST_OF_COUNTIES
        self.template_values["check_ngo_url"] = "/api/ngo/check-url/"
        self.template_values["ngo_upload_url"] = url_for("api-ngo-upload-url")

        ong_nume = request.form.get('ong-nume')

        ong_logo_url = request.form.get('ong-logo-url')
        # this file should be received only if js is disabled

        ong_logo = request.form.get('ong-logo') if ong_logo_url is None else None

        ong_descriere = request.form.get('ong-descriere')

        ong_tel = request.form.get('ong-tel', "")
        ong_email = request.form.get('ong-email', "")
        ong_website = request.form.get('ong-website', "")

        ong_adresa = request.form.get('ong-adresa')
        ong_judet = request.form.get('ong-judet', "")

        ong_cif = request.form.get('ong-cif')
        ong_account = request.form.get('ong-cont')
        ong_special_status = request.form.get('special-status') == "on"

        ong_url = request.form.get('ong-url')
        ong_id = request.form.get('ong-id', 0)

        # validation
        if not ong_nume or not ong_descriere or not ong_adresa or not ong_url or not ong_cif or not ong_account:
            self.template_values["errors"] = incomplete_form_data
            return render_template(self.template_name, **self.template_values)

        # If the user is Admin, then try to load the NGO specified by id
        if user.is_admin:
            ngo = NgoEntity.query.filter_by(id=ong_id).first()
        else:
            ngo = None

        # If no NGO was specified by id, then try to load the user's NGO
        if not ngo:
            ngo = user.ngo

        # update the selected ngo
        if ngo:

            # TODO: Remove this useless null check
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

                ngo.email = ong_email
                ngo.website = ong_website
                ngo.tel = ong_tel

                ngo.special_status = ong_special_status

                # if no one uses this CIF
                if ong_cif != ngo.cif:
                    cif_unique = NgoEntity.query.filter_by(cif=ong_cif).first() is None
                    if cif_unique:
                        ngo.cif = ong_cif
                    else:
                        self.template_values["unique"] = False
                        return render_template(self.template_name, **self.template_values)

                # and no one uses this bank account
                if ong_account != ngo.account:
                    acc_unique = NgoEntity.query.filter_by(account=ong_account).first() is None
                    if acc_unique:
                        ngo.account = ong_account
                    else:
                        self.template_values["unique"] = False
                        return render_template(self.template_name, **self.template_values)

                if user.is_admin:
                    ngo.verified = request.form.get('ong-verificat') == "on"
                    ngo.active = request.form.get('ong-activ') == "on"

                    # if we want to change the url
                    if ong_url != ngo.form_url:

                        is_ngo_url_available = check_ngo_url(ong_url)

                        if not is_ngo_url_available:
                            self.template_values["errors"] = url_taken
                            return render_template(self.template_name, **self.template_values)

                        # new_key = Key(NgoEntity, ong_url)

                        # # replace all the donors key
                        # donors = Donor.query(Donor.ngo == ngo.key).fetch()
                        # if donors:
                        #     for donor in donors:
                        #         donor.ngo = new_key
                        #         donor.put()

                        # # replace the users key
                        # ngos_user = User.query(Donor.ngo == ngo.key).get()
                        # if ngos_user:
                        #     ngos_user.ngo = new_key
                        #     ngos_user.put()

                        # # copy the old model
                        # new_ngo = ngo
                        # # delete the old model
                        # ngo.key.delete()
                        # # add a new key
                        # new_ngo.key = new_key

                        # ngo = new_ngo

                # save the changes
                db.session.merge(ngo)
                db.session.commit()

                if user.is_admin:
                    return redirect(url_for("admin-ong", ngo_url=ngo.url))
                else:
                    return redirect(url_for("asociatia"))

        # create a new ngo entity
        # do this before validating the url, cif and back account because if we have errors 
        # to at least prepopulate the form on refresh
        new_ngo = NgoEntity(
            url=ong_url,

            name=ong_nume,
            description=ong_descriere,
            logo=ong_logo_url,

            email=ong_email,
            website=ong_website,
            tel=ong_tel,

            address=ong_adresa,
            county=ong_judet,

            cif=ong_cif,
            account=ong_account,
            special_status=ong_special_status
        )

        # check for unique url
        is_ngo_url_available = check_ngo_url(ong_url)
        if not is_ngo_url_available:
            self.template_values["errors"] = url_taken

            # new_ngo.key = None
            self.template_values["ngo"] = new_ngo

            return render_template(self.template_name, **self.template_values)

        unique = NgoEntity.query.filter((NgoEntity.cif == ong_cif) | (NgoEntity.account == ong_account)).first() is None

        if not unique:
            # asks if he represents the ngo

            self.template_values["errors"] = not_unique
            return render_template(self.template_name, **self.template_values)
        else:
            self.template_values["errors"] = True

        if user.is_admin:

            # a list of email addresses
            new_ngo.other_emails = [s.strip() for s in request.form.get('alte-adrese-email', "").split(",")]

            db.session.merge(new_ngo)
            db.session.commit()

            return redirect(url_for("admin-ong", ngo_url=ong_url))
        else:
            # link this user with the ngo
            # the ngo has a key even though we haven't saved it, we offered it an unique id
            # user.ngo = new_ngo.key

            # # use put_multi to save rpc calls
            # put_multi([new_ngo, user])

            # try:
            #     subject = "O noua organizatie s-a inregistrat"
            #     values = {
            #         "ngo": ong_nume,
            #         "link": request.form.host + '/' + new_ngo.key.id()
            #     }
            #     body = self.jinja_enviroment.get_template("email/admin/new-ngo.txt").render(values)
            #     # info(body)
            #     mail.send_mail(sender=CONTACT_EMAIL_ADDRESS, to="donezsieu@gmail.com", subject=subject, body=body)
            # except Exception as e:
            #     info(e)

            # do a refresh
            return redirect(url_for("contul-meu"))
