

from appengine_config import AWS_PDF_URL
from google.appengine.api import urlfetch


upload_file_url = '/upload-file'


class UploadHandler(object):
    """handler used to upload files to S3"""

    def upload_file_to_s3(file_to_upload):
        """ TODO: implement this. it doesn't work right now
        returns s3 file url """
        file_name = file_to_upload.name
        file_type = file_to_upload.type
        
        response = urlfetch.fetch(url=AWS_PDF_URL + "/upload-file" + "?file_name="+file_name + "&file_type="+file_type)

        response = json.loads(response)
        signed_request = response.signed_request

        try:
            result = urlfetch.fetch(url=signed_request, method="PUT", data=file_to_upload)
            if result.status_code == 200:
                return response.url

        except Exception, e:
            pass