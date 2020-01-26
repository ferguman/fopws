from datetime import datetime, timedelta
from sys import exc_info
import csv
import io
import json

from logger import get_sub_logger
from DbConnection import DbConnection
from config.config import dbconfig
from nacl_fop import decrypt_dict_vals

logger = get_sub_logger('data')


def get_device_data_json(device_uuid, start_date, end_date, utc_offset):

    try:
        q = """select ea.name as attribute, seo.units as units, seo.utc_timestamp + interval '%s' hour as sample_time, seo.measurement_value as value,
               d.local_name as device_local_name, es.name as subject_name, esl.location_guid as subject_location_id
               from  environment_observation as eo 
                     inner join scalar_environment_observation as seo on eo.id = seo.environment_observation_id
                     inner join environment_attribute as ea on eo.environment_attribute_id = ea.id
                     inner join environment_subject_location as esl on esl.guid = eo.environment_subject_location_guid
                     inner join environment_subject as es on esl.environment_subject_id = es.id
                     inner join device as d on d.guid = eo.participant_guid 
               where eo.participant_guid = %s and utc_timestamp >= timestamp %s and utc_timestamp < timestamp %s
               order by seo.utc_timestamp desc;
             """ 

        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:

            # Note: We convert time filters from the user's local time to utc.
            cur.execute(q, (utc_offset, device_uuid, 
                            datetime.strptime(start_date, '%Y-%m-%d') - timedelta(hours=utc_offset),
                            datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(hours=utc_offset)))

            rc = cur.rowcount
            
            if rc == 0:
               logger.warning('No device data available')
               return json.dumps('No device data available') 

            obs_list = []
            for record in cur:
                #- obs = {'value_name': None}
                obs = {'type': 'environment'} 
                obs['device_name'] = record[4] 
                obs['device_id'] = device_uuid 
                obs['subject'] =  record[5] 
                obs['subject_location_id'] = record[6] 
                obs['attribute'] = record[0] 
                obs['value'] = record[3] 
                obs['units'] = record[1] 
                #- obs['ts'] = record[2].strftime('%c') 
                obs['ts'] = record[2].isoformat()
                obs_list.append(obs)

            return json.dumps(obs_list, indent=3)

    except:
        logger.error('in get_device_data_json: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return None 

def get_device_data(out_fp, device_uuid, start_date, end_date, utc_offset):

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

        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:

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
