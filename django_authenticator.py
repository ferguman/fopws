import datetime
import hashlib
from decimal import Decimal

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
    return hashlib.pbkdf2_hmac(digest().name, password, salt, iterations, dklen)
