import boto3
from sys import exc_info
import io

from logger import get_sub_logger 
from nacl_fop import decrypt
from config.config import image_file_bucket_name, fop_aws_access_key_id_b64_cipher, fop_aws_secret_access_key_b64_cipher

logger = get_sub_logger('boto3_fop')

class S3Session():

    def __init__(self):
        pass

    def __enter__(self):
        try:

            self.s3 = boto3.Session(aws_access_key_id=decrypt(fop_aws_access_key_id_b64_cipher).decode('utf-8'),
                                     aws_secret_access_key=decrypt(fop_aws_secret_access_key_b64_cipher).decode('utf-8'), 
                                     region_name="us-east-2").resource('s3')
            return self

        except:
            logger.error('Exception encountered while connecting to s3: {}, {}, {}'.format(
                exc_info()[0], exc_info()[1], exc_info()[2]))
            raise

    def __exit__(self, exc_type, exc_value, exc_trace):
        # Note: The boto3 docs do not contain any indication that one needs to close S3 sessions. I think the
        #       the network calls are probably stateless so one needs only manage session clients with no need to
        #       worry about sending close commands over the network.
        pass

    def get_s3_image(self, s3_file_key):

        try:
            with io.BytesIO() as data:
                self.s3.Bucket(image_file_bucket_name).download_fileobj(s3_file_key, data)
                r = {'image_blob':data.getvalue()}
                return r

        except:
            logger.error('error connecting to s3: {}:{}:{}'.format(exc_info()[0], exc_info()[1], exc_info()[2]))
            return {'image_blob':None, 'msg':'error occured during s3 image retreival'}

# TODO: make this a method of the S3Session object
def send_file_to_s3(f: 'Open File', file_name: 'uuid'):

    try:
        session = boto3.Session(aws_access_key_id=decrypt(fop_aws_access_key_id_b64_cipher).decode('utf-8'),
                                aws_secret_access_key=decrypt(fop_aws_secret_access_key_b64_cipher).decode('utf-8'), 
                                region_name="us-east-2")
    
        s3 = session.resource('s3')

        s3.Bucket(image_file_bucket_name).put_object(Key=file_name.hex, Body=f)

    except:
        logger.error('Exception encountered while uploading file to S3: {},{},{}'.format(
            exc_info()[0], exc_info()[1], exc_info()[2]))
        raise

"""-
def get_s3_image(s3_file_key):

    try:

        s3 = boto3.Session(aws_access_key_id=decrypt(fop_aws_access_key_id_b64_cipher).decode('utf-8'),
                           aws_secret_access_key=decrypt(fop_aws_secret_access_key_b64_cipher).decode('utf-8'), 
                           region_name="us-east-2").resource('s3')

        with io.BytesIO() as data:
            s3.Bucket(image_file_bucket_name).download_fileobj(s3_file_key, data)
            r = {'image_blob':data.getvalue()}
            return r

    except:
        logger.error('error connecting to s3: {}:{}'.format(exc_info()[0], exc_info()[1]))
        return {'image_blob':None, 'msg':'error occured during s3 image retreival'}
"""
