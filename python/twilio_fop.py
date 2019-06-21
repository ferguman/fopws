from twilio.rest import Client

from config.config import twilio_account_sid_b64_cipher, twilio_auth_token_b64_cipher, twilio_from_number_b64_cipher
from logger import get_sub_logger 
from nacl_fop import decrypt

logger = get_sub_logger('twilio_fop')

def send_text(text_number, body):

    try:

        client = Client(decrypt(twilio_account_sid_b64_cipher), twilio(twilio_auth_token_b64_cipher))

        message = client.messages\
            .create(
                body = body,
                from_ = decrypt(twilio_from_number_b64_cipher),
                to = text_number) 

        return {'error': False}

    except:

        logger.error('function: send_text, exception: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return {'error': True}
