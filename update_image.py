from datetime import datetime
from sys import exc_info
from os import path

from flask import current_app
import boto3
import botocore

from private_settings import fop_aws_access_key_id, fop_aws_secret_access_key, image_file_bucket_name


def get_latest_s3_image_file_key(device_id):

    return 'fa586d7ea2974071960323b9bcbb0eac'

def fetch_s3_file(s3_file_key, destination):

    session = boto3.Session(aws_access_key_id=fop_aws_access_key_id,
                            aws_secret_access_key=fop_aws_secret_access_key, 
                            region_name="us-east-2")
    
    s3 = session.resource('s3')

    try:

        s3.Bucket(image_file_bucket_name).download_file(s3_file_key, destination) 
        return True

    except botocore.exceptions.ClientError as e:

        if e.response['Error']['Code'] == "404":
            current_app.logger.error('The S3 object {} does not exist'.format(s3_file_key))
            return False
        else:
            raise


def get_s3_image(device_id):

       return fetch_s3_file(get_latested_s3_image_name(device_id), 'static/image.jpg'),
               
def update_image_file_from_s3(device_id, image_file_path):

    try:
        # Get the s3 image name from postgres
        current_app.logger.info('got here 4')
        return fetch_s3_file(get_latest_s3_image_file_key(device_id), image_file_path)
    except:
        current_app.logger.error('error fetching image from S3: {}, {}'.format(exc_info[0], exc_info[1]))

