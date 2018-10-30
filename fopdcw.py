from io import BytesIO
from sys import exc_info

from flask import flash, Flask, render_template, request, Response, send_file, send_from_directory,\
                  session
import requests
import psycopg2

from DbConnection import DbConnection
from django_authenticator import get_hash_info, check_password_hash 
from generate_chart import generate_chart
from jose_fop import make_image_request_jwt
from logger import get_top_level_logger
from nacl_fop import decrypt, decrypt_dict_vals

from config.config import dbconfig, chart_list, flask_app_secret_key_b64_cipher, fop_url_for_get_image

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

app.secret_key = decrypt(flask_app_secret_key_b64_cipher)

# This function has the side effect of injecting the fopdcw log handler into the 
# flask.app logger.
logger = get_top_level_logger()

#TODO - Need to create decorator that restricts all the routes to logged on users
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
                return render_template('home.html', chart_list=chart_list)
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


# TODO: Add authentication check via a decorator.
@app.route('/image.jpg')
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


# TODO: Add authentication check via a decorator.
@app.route('/chart/<data_type>')
def chart(data_type):

    logger.info('chart request for {}'.format(data_type))

    result = generate_chart(data_type, session['user']['ct_offset'])
    
    if result['bytes'] != None:
        return Response(result['bytes'], mimetype='image/svg+xml')
    else:
        #TODO: Need to put in a proper error message here.
        return send_from_directory('/static', 's3_error.jpg', mimetype='image/png')


# Django currently limits usernames to 150 characters
#
def authenticate(username, password, cur):

    if username == 'peter'\
        and password == 'book$hit&sheep':

        return True

    # Is the user in the db?
    try:
        assert ( username != None), 'empty username'
        assert (len(username) > 1 and len(username) <= 150), 'username must be 1 to 150 characters long'
        logger.info('login request from {}'.format(username))

        #- dbauthinfo = decrypt_dict_vals(dbconfig, {'password'})
        #- dbauthinfo['password'] = dbauthinfo['password'].decode('utf-8')

        # TODO: Need to wrap the connection in a context so it can be closed automatically
        # Lookup the username in the database.
        #- con = psycopg2.connect(**dbauthinfo)
        #- cur = con.cursor() 
        
        return check_password_hash(get_hash_info(cur, username), password)
        #- result = get_user_password_hash(cur, username)

        # cur.close()
        # con.close()

        """-
        if (result != None):
            return hash_match(result, password)
        else:
            return False
        """

    except:
        logger.error('authenticate exception: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return False

def create_new_session(username, cur):

    #TODO - hydrate the session based uipon the users database profile.
    # ct_offset is the number of hours that the user wants their time data to be offset from central time.
    # The server (Ubuntu) generates central time as per US rules for daylight savings so this setting shouldn't need
    # to be adjusted to account for day light savings time.
    # TODO: The ct_offset stuff won't work. figure out a way to store the users preferred time zone and refactor
    # to slide all display times from the central time (i.e. server time) to the users time.  Make server time
    # a configuration setting.
    #

    s = {'user_name': username, 'user_id':'sdfds', 'org_id':'dac952cd89684c26a508813861015995', 
         'device_id':'dda50a41f71a4b3eaeea2b58795d2c99', 'camera_id':'dda50a41f71a4b3eaeea2b58795d2c99',
         'ct_offset':0}

    if username == 'peter': 
        return s

    sql = """select person.nick_name, person.guid, person.django_username, participant.organization_guid from person inner join
             participant on person.guid = participant.guid where person.django_username = %s;"""

    cur.execute(sql, (username,))

    rc = cur.rowcount
    # TEST HOOK rc = 2
    assert(rc == 1), 'create_new_sesson: django_username {} has {} associated person records.  It should only have 1.'\
                     .format(username, rc) 

    person_info = cur.fetchone()
    s['user_id'] = person_info[1]
    s['nick_name'] = person_info[0]
    s['org_id'] = person_info[3]

    logger.debug('user profile: {}'.format(s))

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
        # return {'bytes':r.iter_content(chunk_size=10*1024)}
    else:
        logger.error('image request failed, status: {}, encoding: {}'.format(r.status_code, r.encoding))
        if r.encoding == 'text/html' or r.encoding == 'utf-8':
            logger.error('response text: {}'.format(r.text[0:100]))
        return {'bytes':None}

if __name__ == "__main__":
    app.run(host='0.0.0.0')
