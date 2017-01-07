
import os

import cloudstorage as gcs

from appengine_config import DEV

from google.appengine.api import app_identity

from logging import info

class CloudStorage(object):
    """docstring for CloudStorage"""

    # the file id at the end, it should contain the bucket name
    STORAGE_UPLOAD_URL = "https://storage.googleapis.com{0}"
    # or "https://storage-download.googleapis.com/{0}"
    STORAGE_DOWNLOAD_URL = "https://storage.googleapis.com{0}"
    
    @staticmethod
    def get_bucket_name():
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())

        return bucket_name

    @staticmethod
    def save_file(file_to_save=None, filename=None):
        """Create a file.

        The retry_params specified in the open call will override the default
        retry params for this particular file handle.

        Args:
        filename: filename.
        """


        if file_to_save is None or filename is None:
            return
        
        # when it's user uploaded the file is on the attribute file 
        if hasattr(file_to_save, 'file'):
            file_to_save = file_to_save.file

        # add the bucket name at the begining of the file
        filename = "/{0}/{1}".format(CloudStorage.get_bucket_name(), filename)

        write_retry_params = gcs.RetryParams(backoff_factor=1.1)
        gcs_file = gcs.open(filename,
                          'w',
                          # String. Used only in write mode. 
                          # You should specify the MIME type of the file (You can specify any valid MIME type.) 
                          # If you don't supply this value, Cloud Storage defaults to the type binary/octet-stream 
                          # when it serves the object.
                          content_type=file_to_save.type if hasattr(file_to_save, 'type') else 'application/pdf',
                          # content_type="application/pdf",
                          options={
                            "x-goog-acl": "public-read"
                          },
                          # options={'x-goog-meta-foo': 'foo',
                                   # 'x-goog-meta-bar': 'bar'},
                          retry_params=write_retry_params)


        if hasattr(file_to_save, 'read'):
            gcs_file.write( file_to_save.read() )
        
        else: 
          return None

        gcs_file.close()

        # if we are on dev we will be using the blobstore to simulate cloud storage
        if DEV:
            # Note: files are stored in the /tmp folder, so not permanent
            file_url = gcs.common.local_api_url() + filename
        else:
            file_url = CloudStorage.STORAGE_DOWNLOAD_URL.format( filename )

        return file_url

        

    def read_file(self, filename):

        gcs_file = gcs.open(filename)
        info(gcs_file.readline())
        
        gcs_file.seek(-1024, os.SEEK_END)
        info(gcs_file.read())
        
        gcs_file.close()
