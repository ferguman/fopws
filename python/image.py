from datetime import datetime, timedelta
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

    # Get the file names of the images that are statisfy the start and end dates
    with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:

        sql = """select s3_reference, utc_timestamp from phenotype_observation inner join phenotype_image on
                 phenotype_observation.id = phenotype_image.phenotype_observation_id where
                 phenotype_observation.participant_guid = %s and
                 phenotype_observation.utc_timestamp >= %s and 
                 phenotype_observation.utc_timestamp < %s order by
                 phenotype_observation.utc_timestamp desc;"""

        # Get the dates in the right shape
        sd = datetime.strptime(start_date, '%Y-%m-%d')
        ed = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        logger.info('sql {}'.format(sql))        
        logger.info('{} {} {}'.format(camera_uuid, sd, ed))

        cur.execute(sql, (camera_uuid, sd, ed))
        assert(cur.rowcount > 0), 'No images are available for this camera.'

        image_period = 24 // int(images_per_day)  #// is for floor division e.g. 3/2 = 1.
        assert image_period != 0, 'error: image_period cannot be zero'

        current_date = None
        current_date_observations = []
        all_observations = []

        # Filter to limit to n images per day where n equals images_per_day.
        for observation in cur.fetchall():

            if current_date == None or current_date != observation[1].date():
                #- all_observations.extend([co['s3_reference'] for co in current_date_observations])
                all_observations.extend(current_date_observations)
                current_date = observation[1].date()
                current_date_observations = [{'s3_reference':observation[0],
                                              'utc_timestamp':observation[1],
                                              'period_index':observation[1].hour // image_period}]
                next 

            if not observation[1].hour // image_period in\
               [observation['period_index'] for observation in current_date_observations]:

                current_date_observations.append({'s3_reference':observation[0],
                                                  'utc_timestamp':observation[1],
                                                  'period_index':observation[1].hour // image_period})

    # add any observations that are left over from the last day processed in the loop above.
    # Note that the extend method returns None so one cannot return the expression below as the list.
    #
    all_observations.extend(current_date_observations)
    
    return all_observations
