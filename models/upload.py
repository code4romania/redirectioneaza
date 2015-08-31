

from appengine_config import AWS_PDF_URL
from google.appengine.api import urlfetch

import json

from urllib import urlencode
from logging import info

upload_file_url = '/upload-file'


class UploadHandler(object):
    """handler used to upload files to S3"""

    @staticmethod
    def get_signed_url(file_name, file_type):

        if not file_type or not file_type:
            return False

        full_url = AWS_PDF_URL + "/upload-file?" + urlencode({"file_name":file_name, "file_type":file_type})

        try:
            # try and fetch a response
            response = urlfetch.fetch(url=full_url, method="GET")
            if response.status_code == 200:
                return json.loads(response.content)
        
        except Exception, e:
            info(e)
    
        return False
                

    def upload_file_to_s3(file_to_upload):
        """ TODO: implement this. it doesn't work right now
        returns s3 file url """
        file_name = file_to_upload.name
        file_type = file_to_upload.type
        
        response = self.get_signed_url(file_name, file_type)

        signed_request = response.signed_request

        try:
            result = urlfetch.fetch(url=signed_request, method="PUT", data=file_to_upload)
            if result.status_code == 200:
                return response.url

        except Exception, e:
            pass