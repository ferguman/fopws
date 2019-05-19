from logger import get_sub_logger

from python.boto3_fop import get_s3_image

logger = get_sub_logger('image')

def get_image_file_v2(s3_file_key):

    """ TODO - finish the docs and the code for this routine """
    return get_s3_image(s3_file_key)


def get_newest_image_uuid(camera_uuid):

    """ TODO - finish the docs and the code for this routine """

    return '0242eb9b34d24c5ba216e4d1efdb8f92'
