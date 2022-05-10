
import urllib2, urllib

from datetime import datetime
from hashlib import sha1

from google.appengine.ext.ndb import Key
from google.appengine.api import users, urlfetch

from models.models import NgoEntity, Donor, Job
from models.handlers import BaseHandler, AccountHandler, user_required
from models.storage import CloudStorage
from models.create_pdf import create_pdf

from appengine_config import PRODUCTION, USER_UPLOADS_FOLDER, DEFAULT_NGO_LOGO, DOMAIN, ZIP_WORKER

from webapp2_extras import json, security

from logging import info, exception, warn


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
                "logo": ngo.logo if ngo.logo else DEFAULT_NGO_LOGO,
                "active_region": ngo.active_region,
                "description": ngo.description
            })

        self.return_json(response)

class GetNgoForm(BaseHandler):

    def get(self, ngo_url):
        
        ngo = NgoEntity.get_by_id(ngo_url)

        if not ngo:
            self.abort(404)

        # if we have an form created for this ngo, return the url
        if ngo.form_url:
            self.redirect(str(ngo.form_url), abort=True)

        # else, create a new one and upload to GCS for future use
        ngo_dict = {
            "name": ngo.name,
            "cif": ngo.cif,
            "account": ngo.account,
            # do not add any checkmark on this form regarding the number of years
            "years_checkmark": False,
            # "two_years": False,
            "special_status": ngo.special_status
        }
        donor = {
            # we assume that ngos are looking for people with income from wages
            "income": "wage"
        }
        pdf = create_pdf(donor, ngo_dict)

        # filename = "Formular 2% - {0}.pdf".format(ngo.name)
        filename = "Formular_donatie.pdf"
        ong_folder = security.hash_password(ngo.key.id(), "md5")
        path = "{0}/{1}/{2}".format(USER_UPLOADS_FOLDER, str(ong_folder), filename)

        file_url = CloudStorage.save_file(pdf, path)

        # close the file after it has been uploaded
        pdf.close()

        ngo.form_url = file_url
        ngo.put()

        self.redirect(str(ngo.form_url))


class GetNgoForms(AccountHandler):

    @user_required
    def post(self):
        ngo = self.user.ngo.get()

        now = datetime.now()
        start_of_year = datetime(now.year, 1, 1, 0, 0)

        # get all the forms that have been completed since the start of the year
        # and they are also signed
        urls = Donor.query(Donor.date_created > start_of_year and Donor.has_signed == True).fetch(projection=['pdf_url'])
        # extract only the urls from the array of models
        urls = [u.pdf_url for u in urls]

        # test data
        # urls = [
        #     "https://storage.googleapis.com/redirectioneaza/documents/202cb962ac59075b964b07152d234b70/112a1636d10a55105b9dd6477fd9ea3c6afa9c0c"
        # ]

        # if no forms
        if len(urls) == 0:
            return self.redirect(self.uri_for('contul-meu'))

        # create job
        job = Job(
            ngo=ngo.key, 
            owner=self.user.key
        )
        job.put()

        export_folder = security.hash_password(ngo.key.id(), "md5") if PRODUCTION else 'development'
        # make request
        params = json.encode({
            "urls": urls,
            "path": "exports/{}/export-{}.zip".format(export_folder, job.key.id()),
            "webhook": {
                "url": "{}{}".format(DOMAIN, self.uri_for('webhook')),
                "data": {
                    "jobId": job.key.id()
                }
            }
        })

        request = urllib2.Request(
            url = ZIP_WORKER,
            data = params,
            headers = {
                "Content-type": "application/json"
            }
        )

        try:
            httpresp = urllib2.urlopen(request)

            response = json.decode( httpresp.read() )
            info(response)

            httpresp.close()

        except Exception, e:
            exception(e)

            # if job failed to start remotely
            # job.key.delete()

        finally:
            self.redirect(self.uri_for('contul-meu'))


class Webhook(BaseHandler):

    def post(self):
        body = json.decode(self.request.body)

        data = body.get('data')
        url = body.get('url')

        # mark the job as done
        job = Job.get_by_id(data.get('jobId'))

        if not job:
            exception('Received an webhook. Could not find job with id {}'.format(data.get('jobId')))

        if job.status == 'done':
            warn('Job with id {} is already done. Duplicate webhook'.format(job.key.id()))

        job.status = 'done'
        job.put()

        owner = job.owner.get()

        # send email
        self.send_dynamic_email(template_id='d-312ab0a4221944e3ac728ae08c504a7c', email=owner.email, data={"link": url})

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
