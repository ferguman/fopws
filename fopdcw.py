from io import BytesIO
from logging import INFO, DEBUG, getLogger
from sys import exc_info

from flask import flash, Flask, render_template, request, Response, send_file, send_from_directory, session
import requests

from fopdcw_logger import get_top_level_logger
from generate_chart import generate_chart
from jose_fop import make_image_request_jwt

from config.config import fop_url_for_get_image

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

# TODO: Move the secret key to a "secure store"
app.secret_key = b'x4gfl}SbJR;zCUO&Kk0twJ:EBhz/ZEu'

# This function has the side effect of injecting the fopdcw log handler into the werkzeug and
# flask.app loggers.
logger = get_top_level_logger()

# Inject the gunicorn log handlers into Flask
#- app.logger.handlers = getLogger('gunicorn.error').handlers
# Set the Flask log level - this has no impact Gunicorn's log level
# TODO - Move the logging level to the configuration file
# app.logger.setLevel(DEBUG)

#TODO - Need to create decorator that restricts all the routes to logged on users
@app.route("/login", methods=['GET'])
@app.route("/")
def get_login_form():
     # show the login form 
     return render_template('login.html', error=None)

@app.route("/login", methods=['POST'])
def process_login():

    error = None

    if authentic(request.form['username'], request.form['password']):
        session['user'] = create_new_session(request.form['username'])
        flash('login succesful')
        return render_template('home.html')
    else:
        session['user'] = None
        flash('incorrect username or password')
        #- error = 'incorrect username or password'
        #- return render_template('login.html', error=error)
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
            #- return Response(BytesIO(result['bytes']), mimetype='image/jpg')
            #- return send_file(BytesIO(result['bytes']), mimetype='image/png')
        else:
            return send_from_directory(os.path.join(app.root_path, 'static'), 's3_error.jpg', mimetype='image/png')
    except:
        logger.error('in /image.jpg route: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return send_from_directory('/static', 's3_error.jpg', mimetype='image/png')


# TODO: Add authentication check via a decorator.
@app.route('/chart/<data_type>')
def chart(data_type):

    logger.info('chart request for {}'.format(data_type))

    result = generate_chart(data_type)
    
    if result['bytes'] != None:
        return Response(result['bytes'], mimetype='image/svg+xml')
    else:
        #TODO: Need to put in a proper error message here.
        return send_from_directory('/static', 's3_error.jpg', mimetype='image/png')

def authentic(username, password):
    #TODO - authenticate against the fop db
    return username == 'ferguman' and password == 'wood$lye9sheep'

def create_new_session(username):

    #TODO - the device id needs to be looked up based upon the username
    s = {'user_name': username, 'user_id':'sdfds', 'org_id':'dac952cd89684c26a508813861015995', 
         'device_id':'dda50a41f71a4b3eaeea2b58795d2c99', 'camera_id':'dda50a41f71a4b3eaeea2b58795d2c99'}

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
