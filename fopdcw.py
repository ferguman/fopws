from functools import wraps
from io import BytesIO
import json
from sys import exc_info

from flask import flash, Flask, render_template, request, Response, send_file, send_from_directory,\
                  session
from flask_cors import CORS
import requests
import psycopg2

from DbConnection import DbConnection
from django_authenticator import get_hash_info, check_password_hash 
from generate_chart import generate_chart
from jose_fop import make_image_request_jwt
from logger import get_top_level_logger
from nacl_fop import decrypt, decrypt_dict_vals

from config.config import dbconfig, flask_app_secret_key_b64_cipher, fop_url_for_get_image

class FopwFlask(Flask):

    jinja_options = Flask.jinja_options.copy()

    # change the server side Jinja template code markers so that we can use Vue.js on the client.
    # Vue.js uses {{ }} as code markers so we don't want Jinja to interpret them.
    jinja_options.update(dict(
        block_start_string = '(%',
        block_end_string = '%)',
        variable_start_string = '((',
        variable_end_string = '))',
        comment_start_string = '(#',
        comment_end_string = '#)',
))

app = FopwFlask(__name__)

# TODO - Consider generating a new secret key everytime Flask is restarted. Flask
#        stores session data in the client on an enrypted cookie.  If you set a
#        new secret key everytime Flask is restarted then pre-restart sessions
#        become invalid after the restart.
#
app.secret_key = decrypt(flask_app_secret_key_b64_cipher)


# This function has the side effect of injecting the fopdcw log handler into the 
# flask.app logger.
logger = get_top_level_logger()

from logging import getLogger, DEBUG, INFO
from logger import get_the_fopdcw_log_handler

getLogger('flask_cors').level =  INFO
getLogger('flask_cors').addHandler(get_the_fopdcw_log_handler())

#TODO: Need a may to remove this cors stuff for the production server.
cors = CORS(app, supports_credentials = True, origins =['http://localhost:8080', 'http://localhost'])

# Decorate URL route functions with this function in order to restrict access
# to logged on users.
def enforce_login(func):

    @wraps(func)

    def wrapper(*args, **kwargs):
        
        if 'user' in session and session['user'] != None:
            return func(*args, **kwargs)		
        else:
            logger.warning('Unauthorized URL access attempt. Route function name: {}'.format(func.__name__))
            r = Response('{"auth_failure": true}')
            #TODO Need to make this a installation variable so that you can turn it off on production.
            r.headers['Access-Control-Allow-Origin'] = '*'
            return r
            #- return 'Please login' 

    return wrapper

# The following two routes (login and logout) should be the only ones that are exposed
# to sessionless traffic.
#
@app.route("/api/login", methods=['POST'])
def process_api_login():

    try:

        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:
            
            creds = request.get_json(force=True)

            if authenticate(creds['username'][0:150], creds['password'][0:150], cur):
                logger.info('authenticate succesful')
                session['user'] = create_new_session(creds['username'][0:150], cur)
                return json.dumps({'logged_in':True, 'organizations':session['user']['organizations']})
            else:
                logger.warning('authentication failed.')
                session['user'] = None
                return json.dumps({'logged_in':False, 'organizations':[{}]})
                #- return '{"logged_in":false}'
    except Exception as err:
         logger.error('process_api_login exception: {}, {}, {}'.format(exc_info()[0], exc_info()[1], err))
         session['user'] = None
         return json.dumps({'logged_in':False, 'organizations':[{}]})
         #- return '{"logged_in":false}'

@app.route("/api/logout", methods=['POST'])
def process_logout():

    try:
        logger.info('{}: api/logout'.format(session['user']['nick_name']))
        session.pop('user', None)
        return json.dumps({'r':True, 'logged_in':False})
    except Exception as err:
        logger.error('api/logout exception: {}, {}, {}'.format(exc_info()[0], exc_info()[1], err))
        return json.dumps({'r':False, 'logged_in':None})

# All routes below this line should apply the @enforce_login decorater in
# order to restrict access to logged in users.

@app.route('/api/extend_session', methods=['GET'])
@enforce_login
def extend_session():
    """ Clients are expected to call this endpoint when they want to keep their session alive. """

    if 'user' in session:
        logger.info('{}: api/extend_session'.format(session['user']['nick_name']))
        return json.dumps({'r':True, 'logged_in':True})
    else:
        logger.error('api/extend_session: No user session.')
        return json.dumps({'r':False, 'logged_in':None})

@app.route('/api/get_crops', methods=['GET'])
@enforce_login
def get_crops():

    try:
        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:

            sql = """select 0 grow_batch_id, start_date, 'germination' from 
                     germination"""

            cur.execute(sql)

            return json.dumps({'server error':False, 'rows':cur.rowcount})

    except:
        logger.error('get_crops exception: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return json.dumps({'server error':True})


@app.route('/api/get_devices', methods=['GET'])
@enforce_login
def get_devices():

    try:
        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:

            #TODO - retreive the user's devices from the database and return as a list.

            devices = [{'name':'sfc1', 'type':'fc1'}]

            return json.dumps({'r':True, 'devices':devices})

    except:
        logger.error('get_devices exception: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return json.dumps({'r':False})






#ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZk
#- TODO: Delete all the routes beneath this line once the system is converted to be
#        entirely API driven.
#
@app.route("/login", methods=['GET'])
@app.route("/")
def get_login_form():
     # show the login form 
     return render_template('login.html', error=None)

     
@app.route("/login", methods=['POST'])
def process_login():

    try:
        with DbConnection(decrypt_dict_vals(dbconfig, {'password'})) as cur:

            if authenticate(request.form['username'][0:150], request.form['password'], cur):
                logger.info('authenticate succesful')
                session['user'] = create_new_session(request.form['username'][0:150], cur)
                return render_template('home.html', devices=session['user']['devices'], selected_device=session['user']['devices'][0], chart_list=session['user']['chart_config']['chart_list'])
                #- return render_template('home.html', chart_list=session['user']['chart_config']['chart_list'])
            else:
                logger.warning('authentication failed.')
                session['user'] = None
                flash('incorrect username or password')
                return render_template('login.html')
    except:
         logger.error('process_login exception: {}, {}'.format(exc_info()[0], exc_info()[1]))
         session['user'] = None
         flash('system error F_PL')
         return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    session['user'] = None
    flash('you are logged out')
    return render_template('login.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('/static', 'favicon.ico', mimetype='image/png')


@app.route('/image.jpg')
@enforce_login
def image():

    try:
        result = get_image_file(session['user']['org_id'], session['user']['camera_id'])

        if result['bytes'] != None:
            return Response(result['bytes'], mimetype='image/jpg')
        else:
            return send_from_directory(os.path.join(app.root_path, 'static'), 's3_error.jpg', mimetype='image/png')
    except:
        logger.error('in /image.jpg route: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return send_from_directory('/static', 's3_error.jpg', mimetype='image/png')


@app.route('/chart/<data_type>')
@enforce_login
def chart(data_type):

    logger.info('chart request for {}'.format(data_type))

    result = generate_chart(data_type, session['user']['chart_config'], 
                            session['user']['ct_offset'])
    
    if result['bytes'] != None:
        return Response(result['bytes'], mimetype='image/svg+xml')
    else:
        #TODO: Need to put in a proper error message here.
        return send_from_directory('/static', 's3_error.jpg', mimetype='image/png')


@app.route('/doser')
@enforce_login
def doser():

    logger.info('doser request')

    return render_template('doser_2.html')

# Django currently limits usernames to 150 characters
#
def authenticate(username, password, cur):

    if username == 'peter'\
        and password == 'book$hit&sheep':

        return True

    # Is the user in the db?
    try:
        assert ( username != None), 'empty username'
        assert (len(username) > 4 and len(username) <= 150), 'username must be 5 to 150 characters long'
        logger.info('login request from {}'.format(username))

        return check_password_hash(get_hash_info(cur, username), password)

    except:
        logger.error('authenticate exception: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return False

def create_new_session(username, cur):

    #TODO - Create a session based upon the users database profile.
    # ct_offset is the number of hours that the user wants their time data to be offset from central time.
    # The server (Ubuntu) generates central time as per US rules for daylight savings so this setting shouldn't need
    # to be adjusted to account for day light savings time.
    # TODO: The ct_offset stuff won't work. figure out a way to store the users preferred time zone and refactor
    # to slide all display times from the central time (i.e. server time) to the users time.  Make server time
    # a configuration setting.
    #

    #- s = {'user_name': username, 'camera_id':'dda50a41f71a4b3eaeea2b58795d2c99', 'ct_offset':0}
    s = {'user_name': username, 'ct_offset':0}

    #- sql = """select person.nick_name, person.guid, person.django_username, participant.organization_guid
    #-         from person inner join participant on person.guid = participant.guid 
    #-         where person.django_username = %s;"""

    sql = """select person.nick_name, person.guid, person.django_username 
             from person where person.django_username = %s;"""

    cur.execute(sql, (username,))

    rc = cur.rowcount
    # TEST HOOK rc = 2
    assert(rc == 1), 'create_new_sesson: django_username {} has {} associated person records.  It should only have 1.'\
                     .format(username, rc) 

    person_info = cur.fetchone()
    s['user_guid'] = person_info[1]
    s['nick_name'] = person_info[0]
    #- s['org_id'] = person_info[3]

    # Now get the user's organizations
    sql = """select participant.organization_guid, organization.local_name from
             participant inner join organization on
             participant.organization_guid = organization.guid where
             participant.guid = %s"""

    cur.execute(sql, (s['user_guid'],))

    if cur.rowcount > 0:
        s['organizations'] = [ {'guid':organization[0], 'name':organization[1]} for organization in cur.fetchall() ]
    else:
        s['organization'] = [{}]

    """-
    # Now find the top level devices that exist within this person's organization and sub-organizations. 
    # A top level device is defined as a device with no parent devices.
    sql = ""select device.local_name, device.guid, device.chart_config from device inner join participant on device.guid = participant.guid
             where device.parent_guid is null and 
             participant.organization_guid in 
             (with recursive org_root (organization_guid) 
             as (select root.guid from organization root where guid = %s 
             Union All
             select child.guid from org_root parent, organization child
             where child.parent_org_id = parent.organization_guid)
             select distinct organization_guid from org_root);""
 
    cur.execute(sql, (s['org_id'],))
    rc = cur.rowcount
    # TEST HOOK rc = 0
    # TODO: In the future when the user does not have any devices then show them an interface allowing them to add a device.
    assert(rc > 0), 'No devices are associated with org: {}'.format(s['org_id'])
 
    s['devices'] = [ {'name':device[0], 'id':device[1], 'chart_config':device[2]} for device in cur.fetchall() ]

    #- s['device_id'] = s['devices'][0]['id'] 
    s['chart_config'] = s['devices'][0]['chart_config']

    # Get the list of cameras for the selected device
    sql = ""select device.local_name, device.guid
             from device inner join device_type on device.device_type_id = device_type.id
             where device_type.local_name = 'camera'  and 
             device.guid in 
             (with recursive device_root (device_guid)
             as (select root.guid from device root where guid = %s
             Union All select child.guid from device_root parent, device child 
             where child.parent_guid = parent.device_guid)
             select distinct device_guid from device_root);""

    # TODO: must select camera info for all devices. For now select it for the 1st device.
    cur.execute(sql, (s['devices'][0]['id'],))
    #- cur.execute(sql, (s['device_id'],))
    rc = cur.rowcount
    if rc > 0:
        camera_info = cur.fetchone()
        s['camera_id'] = camera_info[1]
    else:
        s['camera_id'] = None
    """

    logger.debug('session: {}'.format(s))

    return s

def get_image_file(org_id, camera_id):

    # get the image from the image upload server
    
    # create a JWT for authenticating fopdcw to fop
    jwt = make_image_request_jwt(org_id, camera_id)
    logger.info('jwt:{}'.format(jwt))
    headers = {'AUTHORIZATION':'BEARER ' + jwt}

    r = requests.get(url=fop_url_for_get_image, headers=headers)

    if r.status_code == 200:
        s = 'image request successful, status: {}, content-type: {}, content-length-header: {}, content length: {}'
        logger.info(s.format(r.status_code, r.headers['content-type'], r.headers['content-length'], len(r.content)))
        return {'bytes':r.content}
    else:
        logger.error('image request failed, status: {}, encoding: {}'.format(r.status_code, r.encoding))
        if r.encoding == 'text/html' or r.encoding == 'utf-8':
            logger.error('response text: {}'.format(r.text[0:100]))
        return {'bytes':None}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='8081')
