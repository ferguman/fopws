# TODO: Turn this module into a jose interface for the python-jose library. Then 
#       it can be used by fopd, fopdcw, and fop systems as a library.

from base64 import standard_b64encode
from datetime import datetime, timezone
from hashlib import sha256
from time import time
from uuid import uuid4
from logging import getLogger

from requests import post
from jose import jws 

from nacl_fop import decrypt

from config.private_key import fop_jose_id, fopdcw_jose_id
from config.config import jws_secret_key_b64_enc

from logger import get_sub_logger 

# Note: This module uses JWT security (via jose).  Paseto is another system for implemeting token based security.

logger = get_sub_logger('jose_fop') 

def extract_timestamp(path_name) -> 'timestamp':

    dt = path_name.split("/")[-1].split(".")[0]

    return datetime(int(dt[0:4]), int(dt[4:6]), int(dt[6:8]), 
                    hour=int(dt[9:11]), minute=int(dt[12:14]), second=int(dt[15:17]), tzinfo=timezone.utc).timestamp()


def get_jwt_issuer(jws_value: 'jws b64encoded json') -> str:
   
    # Split X.Y.Z, decode Y, interpret as JSON and then extract the JSON attribute named iss. 
    # TODO - Note the padding on the b64 value. Python complains that the JWT claims JSON is  
    # not padded correctly if this padding is not added.  Need to research this. It seems
    # messy to add padding. Why don't the strings arrive correctly padded.
    #
    return loads(urlsafe_b64decode(jws_value.split('.', 2)[1].__add__('==')))['iss']


# Make the JWT claim set
def claim_info(device_id, file_hash, time_stamp, camera_id):

    #- TODO: Time delivers seconds since unix epoch. Not all systems have the same epoch start date.  There
    #- may be a better way to time stamp the claims.
    issue_time = int(time())

    # See RFC 7519
    return {'iss':device_id,                 #Issuer -> This mvp is the issuer. Use it's secret key to authenticate.
            'aud':fop_jose_id,               #Audience -> identifies the cloud provider that will receive this claim.
            'exp':issue_time + 60,           #Expiration Time
            'sub':camera_id,                 #Subject -> This mvp's camera is the subject
            'nbf':issue_time - 60,           #Not Before Time
            'iat':issue_time,                #Issued At
            'jti':str(uuid4()),              #JWT ID -> Don't accept duplicates by jti
            'file_dt':time_stamp,
            'file_hash':file_hash}

def get_image_request_claim(org_id, camera_id):

    issue_time = int(time())

    # See RFC 7519
    return {'iss':fopdcw_jose_id,     # Issuer -> this fopdcw is the issuer. Use it's secret key to authenticate.
            'aud':fop_jose_id,        # Audience -> identifies the cloud provider that will receive this claim.
            'exp':issue_time + 60,    # Expiration Time
            'sub':camera_id,          # TODO: figure out what schema to use for subjects 
            'nbf':issue_time - 60,    # Not Before Time
            'iat':issue_time,         # Issued At
            'jti':str(uuid4()),       # JWT ID -> Don't accept duplicates by jti
            'cam_id':camera_id,       # The camera that took the picture
            'org_id':org_id           # The organization that owns the camera.
            }

def get_file_hash(path_name):

    m = sha256()
    with open(path_name, 'rb') as f:
        for line in f:
            m.update(line)
            
    return standard_b64encode(m.digest()).decode('utf-8')

def get_jws(path_name, camera_id):

    return jws.sign(claim_info(get_file_hash(path_name), extract_timestamp(path_name), camera_id), 
                    decrypt(jws_secret_key_b64_enc),
                    algorithm='HS256')

def make_image_request_jwt(org_id, camera_id):

    return jws.sign(get_image_request_claim(org_id, camera_id), 
                    decrypt(jws_secret_key_b64_enc),
                    algorithm='HS256')

#- TODO: This routine appears to be no longer used.  Confirm and then delete.
def upload_camera_image(path_name, url, camera_id):

    with open(path_name, 'rb') as f:
        r = post('{}'.format(url), 
                 data={'auth_method':'JWS', 'auth_data':get_jws(path_name, camera_id)}, 
                 files={'file':f}) 

    result = r.content.decode('utf-8')
    if result != 'ok':
        logger.error('Image upload error, server response -> {}'.format(result))


def jws_jwt_authenticate(jws_value, issuer_types):
    """ Raise an exception if anything goes wrong. Silent failure is not allowed. """

    if len(jws_value) > 2048:
        logger.warning('JWS JSON was too long.  Strings longer than 2048 are not allowed.')
        raise JwtError('Maleformed JWS')

    if len(jws_value.split('.')) != 3:
        logger.warning('{} period delimited parts found in the JWS. JWS should have 3 parts'.format(len(jwt_parts)))
        raise JwtError('Maleformed JWS')

    try:
        secret_key_value = get_jws_secret_key(jws_value, issuer_types).decode('utf-8') 
        
        decode_settings = {'verify_signature': True, 'verify_aud': True, 'verify_iat': True, 'verify_exp': True, 
                           'verify_nbf': True, 'verify_iss': False, 'verify_sub': False, 'verify_jti': True, 
                           'verify_at_hash': False, 'leeway': 0}

        jwt_claims = jwt.decode(jws_value, secret_key_value, algorithms='HS256',
                                audience=fop_jose_id, options=decode_settings)

        logger.debug('JWS and JWT successfully verified: {}'.format(jwt_claims))

        return jwt_claims

    except:
        logger.warning('JWS and JWT verification failed: {}:{}'.format(exc_info()[0], exc_info()[1]))
        raise

def get_jws_secret_key(jws_value, issuer_types):

    iss_id = get_jwt_issuer(jws_value)
    logger.info('iss_id: {}'.format(iss_id))
    logger.info('issuer_types: {}'.format(issuer_types))
    sk = None
    
    if 'device' in issuer_types:
        sk = get_device_config_item(iss_id, 'hmac_secret_key_b64_cipher_text')

    if sk == None and 'configured' in issuer_types:
        sk = get_configured_issuer_jws_key(iss_id)

    if sk != None:
        return decrypt(sk)
    else:
        logger.warning('unable to find issuer key for issuer: {}'.format(iss_id))
        raise JwtError('cannot find issuer key')

def get_device_config_item(device_id: 'guid', item_name: str) -> str:

   #TODO - this routine has not been tested yet.
   # Get the device's configuration and then extract item_name from it.
   try:
        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:
            sql = """select configuration from device where guid = %s;"""
	    cur.execute(sql, (device_id, ))
	    if cur.rowcount != 1:
	        logger.error('ERROR in get_device_config_item: 0 or more than one devices found with guid {}'.format(device_id))
		return None

            return cur.fetchone()[0][item_name] 

       #- return Device.objects.get(participant_id=device_id).configuration[item_name]
   except:
       logger.warning('item {} not found for device {}'.format(item_name, device_id))
       return None 
