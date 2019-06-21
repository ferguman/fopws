# This file contains settings that control the operation of the fopdcw website.
#
# By convention variables ending with the text 'b64_cipher' are encrypted data.
# To create such a variable run nacl_fop.encrypt(plain_tex). To decrypt and decode such 
# variables run nacl_fop.decrypt(b64_cipher_text)
#
# Note: When setting up a new system first create your private_key.py file and then
# create your config.py file (i.e this file).  The new private key is necessary before
# you can generate new encrypted values in this file.
#

# Give the Flask application a secret it can use to generate session ids
# For new installations generate some random bytes for this variable.
# One way to do this is to use the Python Secrets library as per the commands below:
#    import secrets
#    from nacl_fop import encrypt
#    encrypt(secrets.token_bytes(32))
#
#    The value generated above will look something like: 
#    b'+4Kapb9dryyLzwh0vPEo9cYkPM1RuuBHxVA8urUleWmh3g6EtKhSQQWF8xtFoutDJBLrSevV7Sk3lFyfQirl0lkpbo9EvMhN'
#
#    Cut and paste the value that you generate in the line below as the new
#    value of flask_app_secret_key_b64_cipher
#
flask_app_secret_key_b64_cipher = [FLASK_SECRET_KEY] 

# Postgres database configuration
#
# HOST value is set to a value (e.g. 'localhost') that identifies the host system for the db server. 
# 
# Note: To change a Postgres user's password run the following command from within the psql 
#       application:
#       ALTER USER user_name WITH PASSWORD 'new_password';
# 
# Note that password value is expected to be encrypted b64 encoded cipher text.
# To encrypt and b64 encode the password perform the following from within the Python interetter:
#    from nacl_fop import encrpty
#    encrypt([put the password here as a binary string])
#    Use the value generated above as the value of the 'password' parameter in the dbconfig below.
#
dbconfig = {'host':[HOST],
            'user':[DB_USER],
            'password':[DB_PASSWORD],
            'database':[DB_USER]}

# location of image API 
fop_url_for_get_image = [FOP_URL_FOR_GET_IMAGE]    

# location of couchdb that holds the sensor data
couchdb_location_url = ''
couchdb_username_b64_cipher = ''
couchdb_password_b64_cipher = ''

# fopd signs each JWT claim with a secret key that is shared with the JWT service.  Obtain the
# value from the JWT service to which this installation of fopdw will connect to. Then put
# the b64 encoded cipher text for the secret key as the value of jws_secret_key_b64_enc.
#
# Note: To encrypt and b64 encode the secret key perform the following from within the Python interpretter:
#    from nacl_fop import encrpty
#    encrypt([put the secret key here as a binary string])
#    Use the value generated above as the value of jws_secret_key_b64_enc below.
jws_secret_key_b64_enc = ''

# fopd using Twilio to send SMS messages.
# Note: To encrypt and b64 encode the Twilio information perform the following from within the Python interpretter:
#    from nacl_fop import encrypt
#    encrypt([put the Twilio information here as a binary string])
#    Use the values generated above as the values of the variables below.
twilio_account_sid_b64_cipher = ''
twilio_auth_token_b64_cipher = ''
twilio_from_number_b64_cipher = ''

# Misceallaneous
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL 
log_level = DEBUG

