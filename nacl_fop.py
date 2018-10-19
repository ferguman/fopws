from base64 import standard_b64encode, standard_b64decode

from nacl import secret

from config.private_key import nsk

def encrypt(plain_text):

    return standard_b64encode(secret.SecretBox(standard_b64decode(nsk)).encrypt(plain_text))

def decrypt(ciper_text):

    return secret.SecretBox(standard_b64decode(nsk)).decrypt(standard_b64decode(ciper_text))
