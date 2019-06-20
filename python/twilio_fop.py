from twilio.rest import Client

from logger import get_sub_logger 

logger = get_sub_logger('twilio_fop')

def send_text(text_number, body):

    try:

        #implment twilio send text
        account_sid = 'AC1b3693e000003b02eeb54abbc41d7f24'
        auth_token = '4abcf93c8fe3f3724c7e2675da93489a'

        client = Client(account_sid, auth_token)

        message = client.messages\
            .create(
                body = body,
                from_ = '+13148199768',
                to = '+13144987732') 

        return {'error': False}

    except:

        logger.error('function: send_text, exception: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return {'error': True}
