import os
from flask import flash, Flask, render_template, request, send_from_directory, session
from logging import INFO, DEBUG, getLogger
from sys import exc_info

from update_image import update_image_file_from_s3

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

# Inject the gunicorn log handlers into Flask
app.logger.handlers = getLogger('gunicorn.error').handlers
# Set the Flask log level - this has no impact Gunicorn's log level
# TODO - Move the logging level to the configuration file
app.logger.setLevel(DEBUG)


def authentic(username, password):
    #TODO - authenticate against the fop db
    return username == 'ferguman' and password == 'wood$lye9sheep'

def create_new_session(username):

    #TODO - the device id needs to be looked up based upon the username
    s = {'user_name': username, 'device_id':'dda50a41f71a4b3eaeea2b58795d2c99'}

    return s
  

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

@app.route('/image.jpg')
def image():

    try:
        image_file_dir = os.path.join(app.root_path, 'static') 
        image_file_name = session['user']['device_id'] + 'jpg'
        image_file_path = os.path.join(image_file_dir, image_file_name)

        if update_image_file_from_s3(session['user']['device_id'], image_file_path):
            return send_from_directory(image_file_dir, image_file_name, mimetype='image/png')
        else:
            return send_from_directory(image_file_dir, 's3_error.jpg', mimetype='image/png')

    except:
        app.logger.error('in /image.jpg route: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return send_from_directory(os.path.join(app.root_path, 'static'), 
                                   'image.jpg', mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
