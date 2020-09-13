from config.config import mqtt_url, mqtt_port, mqtt_username,  mqtt_password
from flask_socketio import emit
from logger import get_sub_logger 
from nacl_fop import decrypt
import paho.mqtt.client as mqtt
from sys import exc_info
from time import time

logger = get_sub_logger('repl')

repl_state = {}
repl_state['start_time'] = None 

def uptime():
   return time() - repl_state['start_time']

def start():
   logger.info('starting repl')
   repl_state['start_time'] = time()
   return repl_state 

def make_on_message_handler():
   
   def on_message(client, userdata, message):
      msg = 'MQTT message: userdata: {}, payload: {}'.format(userdata, message.payload.decode('utf-8'))
      logger.info(msg)
      #TODO - need to send this back through the socket io connection to the listener
      emit('response', msg)

   return on_message 

def on_subscribe(mqtt, userdata, mid, granted_qos):
   logger.info('subscribed, data: {}, mid: {}'.format(userdata, mid))


def mqtt_sub():
   # subscribe to all incoming topics
   repl_state['mqtt'].subscribe('#', 2)
   logger.info('subscribing to all MQTT topics')

def mqtt_connect():
   try:
      mqtt_client = mqtt.Client('foobar')
      mqtt_client.on_message = make_on_message_handler()
      mqtt_client.on_subscribe = on_subscribe
      
      # Enforce tls certificate checking 
      mqtt_client.tls_set()
      mqtt_client.enable_logger(logger)

      mqtt_client.username_pw_set(mqtt_username, decrypt(mqtt_password))
      mqtt_client.connect(mqtt_url, mqtt_port, 60)

      # Start the MQTT client - loop_start causes the mqtt_client to spawn a background thread which
      #                         handles the mqtt commuications.  The loop_start call thus returns
      #                         control to this thread immediately.
      mqtt_client.loop_start()
      repl_state['mqtt'] = mqtt_client

      logger.info('started MQTT client')
   except:
      logger.error('Unable to create MQTT client: {} {}'.format(exc_info()[0], exc_info()[1]))
