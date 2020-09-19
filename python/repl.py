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

def up_time():
   return time() - repl_state['start_time']

def make_on_message_handler(repl):
   
   def on_message(client, userdata, message):
      msg = 'MQTT: userdata: {}, payload: {}'.format(userdata, message.payload.decode('utf-8'))
      logger.info(msg)
      #TODO - need to send this back through the socket io connection to the listener
      #- repl_state['emit']('response', msg)
      repl['emit']('response', 'foobar')

   return on_message 

def on_subscribe(mqtt, userdata, mid, granted_qos):
    msg = 'MQTT Ssubscribed, data: {}, mid: {}'.format(userdata, mid)
    logger.info(msg)

def mqtt_sub(repl):
   # subscribe to all incoming topics
   repl['mqtt'].subscribe('#', 2)
   msg = 'subscribing to all MQTT topics'
   repl['emit'](msg)
   logger.info(msg)

def mqtt_connect(repl):
   try:
     
      repl['emit']('response', 'connecting to mqtt..')

      mqtt_client = mqtt.Client('foobar')
      mqtt_client.on_message = make_on_message_handler(repl)
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
      #- repl_state['mqtt'] = mqtt_client
      repl['mqtt'] = mqtt_client

      logger.info('started MQTT client')
   except:
      logger.error('Unable to create MQTT client: {} {}'.format(exc_info()[0], exc_info()[1]))

def apply_cmd(cmd):
   return cmd

def start(request, emitter):
   logger.info('starting repl')
   repl_state['start_time'] = time()
   repl_state['up_time'] = up_time
   repl_state['apply'] = apply_cmd
   return repl_state 
