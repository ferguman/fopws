from DbConnection import DbConnection
from logger import get_sub_logger
from nacl_fop import decrypt_dict_vals
from python.boto3_fop import get_s3_image

from config.config import dbconfig

logger = get_sub_logger('image')

def get_image_file_v2(s3_file_key):

    return get_s3_image(s3_file_key)


def get_newest_image_uuid(camera_uuid):

    """ TODO - finish the docs and the code for this routine """
    
    with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:

        sql = """select s3_reference from phenotype_observation inner join phenotype_image on
                 phenotype_observation.id = phenotype_image.phenotype_observation_id where
                 phenotype_observation.participant_guid = %s order by
                 phenotype_observation.utc_timestamp desc;"""

        cur.execute(sql, (camera_uuid,))
        assert(cur.rowcount > 0), 'No image is available for this camera.'

        return cur.fetchone()[0]

def get_s3_file_names(camera_uuid, images_per_day, start_date, end_date):
    
    return['000412db942f4d858b4adc08e0366bc5', '00011f796735408898dc0c700499743e']
