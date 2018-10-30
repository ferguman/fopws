import datetime
import hashlib
from decimal import Decimal
from sys import exc_info

from logger import get_sub_logger

logger = get_sub_logger(__name__)

# Originally adapted from Django code at https://docs.djangoproject.com/en/2.1/_modules/django/utils/encoding/#is_protected_type
_PROTECTED_TYPES = (
    type(None), int, float, Decimal, datetime.datetime, datetime.date, datetime.time,
)

def is_protected_type(obj):
    """Determine if the object instance is of a protected type.

    Objects of protected types are preserved as-is when passed to
    force_text(strings_only=True).
    """
    return isinstance(obj, _PROTECTED_TYPES)

# Originally adapted from Django code at https://docs.djangoproject.com/en/2.1/_modules/django/utils/encoding/#force_text
#
#
def force_bytes(s, encoding='utf-8', strings_only=False, errors='strict'):

    """
    Similar to smart_bytes, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """

    # Handle the common case first for performance reasons.
    if isinstance(s, bytes):
        if encoding == 'utf-8':
            return s
        else:
            return s.decode('utf-8', errors).encode(encoding, errors)

    if strings_only and is_protected_type(s):
        return s
    if isinstance(s, memoryview):
        return bytes(s)

    # We don't need Promises
    # if isinstance(s, Promise) or not isinstance(s, str):
    #    return str(s).encode(encoding, errors)
    #
    if not isinstance(s, str):
        return str(s).encode(encoding, errors)
    else:
        return s.encode(encoding, errors)


# Originally adpaged from Django code at https://github.com/django/django/blob/master/django/utils/crypto.py
#
# this function works for Django Auth_User:password entries of the form pbkdf2_sha256$(iterations)$(salt)$(b64_hash)
# usage -> base64.b64encode(da.pbkdf2((password), (salt), (iterations)) == (b64_hash)
#
def pbkdf2(password, salt, iterations, dklen=0, digest=None):

    """Return the hash of password using pbkdf2."""

    if digest is None:
        digest = hashlib.sha256
    dklen = dklen or None
    password = force_bytes(password)
    salt = force_bytes(salt)
    # DEBUG ONLY
    # logger.info('digest: {}, password: {}, salt: {}, iterations: {}, dklen: {}'.format(
    #             digest().name, password, salt, iterations, dklen))
    return hashlib.pbkdf2_hmac(digest().name, password, salt, iterations, dklen)

from base64 import b64encode, b64decode
#
# django_hash -> pbkdf2_sha256$(iterations)$(salt)$(b64_hash)
def check_password_hash(django_hash, password) -> bool:

    try:

        # Break out the Django hashing mechanism parts. Note that the hash parts are stored as:
        # (hash_type)$(iterations)$(salt)$(b64_hash)
        hash_parts = django_hash.split('$', 4) 
        assert (hash_parts != None and len(hash_parts) == 4), 'incorrect djanga hash'

        # This code base only supports the standard Django salt method
        assert (hash_parts[0] == 'pbkdf2_sha256'),\
               'unknown django salt method encountered: {}'.format(hash_parts[0][0:13])

        calculated_hash = pbkdf2(password, hash_parts[2] , int(hash_parts[1]), dklen=0, digest=None)
  
        return calculated_hash == b64decode(hash_parts[3]) 


    except:
        logger.error('hash match error: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return False

# returns the Django hash information as  -> (hash_type)$(iterations)$(salt)$(b64_hash)
#
def get_hash_info(cur, username):


    try:
        # TODO: change sql so that it only returns the top 2 records
        sql = """ Select password from Auth_User where username = %s; """
        cur.execute(sql, (username,))

        rc = cur.rowcount
        # TEST HOOK rc = 2
        if rc == 0:        
            logger.warning('User not in database {}'.format(username))
            return None
        elif rc == 1:
            # need to authenticate
            hash_info = cur.fetchone()[0]
            logger.debug('password info: {}'.format(hash_info))
            return hash_info 
        else:
            logger.error('duplicate user found in database {}'.format(username))
            return None
    except:
        logger.error('fault encountered in get_user_password_hash: {}, {}'.format(exc_info()[0], exc_info()[1]))
