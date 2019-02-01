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
# Note that password is the encrypted b64 encoded cipher text generated from the password.
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

jws_secret_key_b64_enc = ''

# Misceallaneous
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL 
log_level = DEBUG

