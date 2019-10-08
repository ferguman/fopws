# TODO: Convert to allow chart data to be pulled from Postgresql database
# TODO: Look at using D3.js as the charting tool

import json
from datetime import datetime, timedelta
from os import getcwd
from sys import exc_info

import pygal
import requests

from logger import get_sub_logger

logger = get_sub_logger('generate_chart')

enable_display_unit_error_msg = None 

# TODO: Current the system supports converting from celsius to fahrenheit. As the need arises
#       add more unit conversions.
#
def apply_unit_conversion(val_tree, chart_info):

    global enable_display_unit_error_msg 

    if 'display_units' in chart_info:
        if chart_info['display_units'].lower() == 'fahrenheit':
            if 'units' in val_tree['value']:
                if val_tree['value']['units'].lower() == 'celsius':
                   return  (float(val_tree['value']['value']) * 9.0/5.0) + 32
                elif val_tree['value']['units'].lower() == 'fahrenheit':
                   return val_tree['value']['value']
                else:
                    # Limit error unit related error messages to once per chart
                    if enable_display_unit_error_msg:
                        logger.error('cannot convert fahrenheit to: {}'.format(val_tree['value']['units']))
                        enable_display_unit_error_msg = False 
                    return val_tree['value']['value']
            else:
                return val_tree['value']['value']
        else:
            # Limit error unit related error messages to once per chart
            if enable_display_unit_error_msg:
                logger.error('non supported display_unit value: {}'.format(chart_info['display_unit']))
                enable_display_unit_error_msg = False 
            return val_tree['value']['value']
    else:
        return val_tree['value']['value']

#Use a view in CouchDB to get the data
#use the first key for attribute type
#order descending so when limit the results will get the latest at the top

from io import BytesIO
#- from config.config import chart_list, couchdb_database_name_b64_cipher, couchdb_location_url, couchdb_password_b64_cipher, couchdb_username_b64_cipher
from config.config import couchdb_location_url, couchdb_password_b64_cipher, couchdb_username_b64_cipher
from nacl_fop import decrypt
import re

def generate_chart_from_couchdb(data_type, couchdb_db_name, chart_info, ct_offset):

    # Get the data from couchdb
    #- couch_query = couchdb_location_url + decrypt(couchdb_database_name_b64_cipher).decode('ascii') + '/'\
    #- couch_query = couchdb_location_url + chart_config['couchdb_db_name'] + '/'\
    couch_query = couchdb_location_url + couchdb_db_name + '/'\
                     + '_design/doc/_view/attribute_value?'\
                     + 'startkey=["{0}","{1}",{2}]&endkey=["{0}"]&descending=true&limit=60'.format(
                     chart_info['attribute'], chart_info['couchdb_name'], '{}')

    logger.debug('prepared couchdb query: {}'.format(couch_query))

    r = requests.get(couch_query, 
                     auth=(decrypt(couchdb_username_b64_cipher).decode('ascii'), 
                           decrypt(couchdb_password_b64_cipher).decode('ascii')))

    #- logger.info('couchdb response: status {}, text {}'.format(r.status_code, r.text))

    if r.status_code == 200:

        try:

            global enable_display_unit_error_msg
            enable_display_unit_error_msg = True
            v_lst = [float(apply_unit_conversion(x, chart_info)) for x in r.json()['rows']]

            td = timedelta(hours=ct_offset)
            ts_lst = [(datetime.fromtimestamp(x['value']['timestamp']) + td).strftime('%m/%d %I:%M %p')\
                      for x in r.json()['rows']]
            ts_lst.reverse()

            line_chart = pygal.Line(x_label_rotation=20, show_minor_x_labels=False)
            line_chart.title = chart_info['chart_title']
            line_chart.y_title= chart_info['y_axis_title']
            line_chart.x_title= chart_info['x_axis_title']

            line_chart.x_labels = ts_lst
            line_chart.x_labels_major = ts_lst[::8]

            #need to reverse order to go from earliest to latest
            v_lst.reverse()

            line_chart.add(chart_info['data_stream_name'], v_lst)
            
            f = line_chart.render()
            return {'bytes':f}
            
        except:
            logger.error('Chart generation failed: {}'.format(exc_info()[0]))
            return {'bytes':None}
    else:
        logger.error('Couchdb returned a bad status code: {}'.format(r.status_code))
        return {'bytes':None}


from DbConnection import DbConnection
from config.config import dbconfig
from nacl_fop import decrypt_dict_vals
def generate_chart_from_postgresql(device_uuid, data_type, chart_info, ct_offset):
    """ data_type is a string formatted as: subject_attribute """

    try:
        #TODO: Need to figure out how to show the times in the timezone as per the user's time zone. 
        q = """select seo.units as units, seo.utc_timestamp at time zone 'CST' as timestamp, seo.measurement_value as value
               from  environment_observation as eo 
                     inner join scalar_environment_observation as seo on eo.id = seo.environment_observation_id
                     inner join environment_attribute as ea on eo.environment_attribute_id = ea.id
                     inner join environment_subject_location as esl on esl.guid = eo.environment_subject_location_guid
                     inner join environment_subject as es on esl.environment_subject_id = es.id
               where participant_guid = %s and es.name = %s and ea.name = %s 
                     and utc_timestamp > now() - '1 day'::interval
               order by seo.utc_timestamp desc
               limit 74;
            """ 

        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:
            sub_att = data_type.split('_', 1)
            cur.execute(q, (device_uuid, sub_att[0], sub_att[1]))
            rc = cur.rowcount
            
            if rc == 0:
               logger.warning('No chart data available')
               return {'bytes':None}

            try:
                global enable_display_unit_error_msg
                enable_display_unit_error_msg = True

                values = cur.fetchall()
                #- v_lst = [float(apply_unit_conversion(x, chart_info)) for x in r.json()['rows']]
                v_lst = [float(apply_unit_conversion({'value':{'units':x[0],'timestamp':x[1],'value':x[2]}}, chart_info))\
                         for x in values]

                td = timedelta(hours=ct_offset)
                #- ts_lst = [(datetime.fromtimestamp(x[1]) + td).strftime('%m/%d %I:%M %p') for x in values]
                ts_lst = [x[1].strftime('%m/%d %I:%M %p') for x in values]
                ts_lst.reverse()

                line_chart = pygal.Line(x_label_rotation=20, show_minor_x_labels=False)
                line_chart.title = chart_info['chart_title']
                line_chart.y_title= chart_info['y_axis_title']
                line_chart.x_title= chart_info['x_axis_title']

                line_chart.x_labels = ts_lst
                line_chart.x_labels_major = ts_lst[::8]

                #need to reverse order to go from earliest to latest
                v_lst.reverse()

                line_chart.add(chart_info['data_stream_name'], v_lst)
            
                f = line_chart.render()
                return {'bytes':f}
            except:       
                logger.error('Chart generation failed while processing postgresql records: {}, {}'\
                             .format(exc_info()[0], exc_info()[1]))
                return {'bytes':None}

    except:
        logger.error('Chart generation failed, postgresql retrieval failed: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return {'bytes':None}


# TODO: implement the ct_offset parameter. It should shift the time ct_offset hours from the 
#       system time. The system time is assumed to be central time hence the name ct_offset.
#
#- def generate_chart(grow_system_uuid, data_type, chart_config, ct_offset):
def generate_chart(device_uuid, data_type, chart_config, ct_offset):

    # first find the chart type that the user is requesting
    chart_info = None
    for chart in chart_config['chart_list']:
        if chart['vue_name'] == data_type:
            chart_info = chart
            break

    if chart_info == None:
        logger.error('Unknown chart type: {}'.format(data_type))
        return {'bytes':None}

    if 'source' in chart_config:
        logger.info('postgresql based chart requested for device {}'.format(device_uuid))
        return generate_chart_from_postgresql(device_uuid, data_type, chart_info, ct_offset)
    else: 
        return generate_chart_from_couchdb(data_type, chart_config['couchdb_db_name'], chart_info, ct_offset)
