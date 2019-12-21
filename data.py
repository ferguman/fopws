from datetime import datetime, timedelta
from sys import exc_info
import csv
import io

from logger import get_sub_logger
from DbConnection import DbConnection
from config.config import dbconfig
from nacl_fop import decrypt_dict_vals

logger = get_sub_logger('data')

def get_device_data(out_fp, device_uuid, start_date, end_date, utc_offset):

        #- cur.execute(q, (device_uuid, start_date, datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)))
        #- session['user']['ct_offset']
    try:
        q = """select ea.name as attribute, seo.units as units, seo.utc_timestamp + interval '%s' hour as sample_time, seo.measurement_value as value
               from  environment_observation as eo 
                     inner join scalar_environment_observation as seo on eo.id = seo.environment_observation_id
                     inner join environment_attribute as ea on eo.environment_attribute_id = ea.id
                     inner join environment_subject_location as esl on esl.guid = eo.environment_subject_location_guid
                     inner join environment_subject as es on esl.environment_subject_id = es.id
               where participant_guid = %s and utc_timestamp >= timestamp %s and utc_timestamp < timestamp %s
               order by seo.utc_timestamp desc;
             """ 
#- and utc_timestamp >= timestamp start_date and utc_timestamp <= timestamp end_date 
#- where participant_guid = %s and es.name = %s and ea.name = %s 

        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:

            #- cur.execute(q, (device_uuid, start_date, datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)))
            #- start_date_utc = datetime.strptime(start_date, '%Y-%m-%d') - timedelta(hours=session['user']['ct_offset']) 
            #- end_date_utc = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)) - timedelta(hours=session['user']['ct_offset'])
            # Note: We convert time filters from the user's local time to utc.
            cur.execute(q, (utc_offset, device_uuid, 
                            datetime.strptime(start_date, '%Y-%m-%d') - timedelta(hours=utc_offset),
                            datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(hours=utc_offset)))

            rc = cur.rowcount
            
            if rc == 0:
               logger.warning('No device data available')
               return False 

            csv_writer = csv.writer(out_fp, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

            rc = 0
            csv_writer.writerow(['attribute', 'unit', 'sample time', 'value'])
            for record in cur:
                csv_writer.writerow(record)
                if rc == 0:
                    logger.info('writing first row {}'.format(out_fp.getvalue()))
                    rc = rc + 1

            out_fp.seek(0)
            return True 

    except:
        logger.error('in get_device_data: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return False
