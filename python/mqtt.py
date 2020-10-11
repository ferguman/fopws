from config.config import mqtt_url, mqtt_port, mqtt_username,  mqtt_password
from flask_socketio import emit
from logger import get_sub_logger 
from nacl_fop import decrypt
import paho.mqtt.client as mqtt
from sys import exc_info
from time import time

logger = get_sub_logger('mqtt')

def up_time(repl_state):
   return time() - repl_state['start_time']

def make_on_message_handler(socketio):
   logger.info('making message handler') 
   socketio.emit('response', 'making message handler')
   def on_message(client, userdata, message):
      msg = 'MQTT: userdata: {}, payload: {}'.format(userdata, message.payload.decode('utf-8'))
      logger.info(msg)
      socketio.emit('response', msg)

   return on_message 

def on_subscribe(mqtt, userdata, mid, granted_qos):
    msg = 'MQTT Subscribed, data: {}, mid: {}'.format(userdata, mid)
    logger.info(msg)

"""-
def mqtt_subscribe_all(repl_state, emit):
   # subscribe to all incoming topics
   repl_state['mqtt_client'].subscribe('#', 2)
   msg = 'subscribing to all MQTT topics'
   emit('response', msg)
   logger.info(msg)
"""

def mqtt_connect(*args):
   """ args[0] = socketio
       args[1] = repl_state """
   try:
     
      #- emit('response', 'connecting to mqtt..')
      args[0].emit('response', 'connecting to mqtt..')

      mqtt_client = mqtt.Client('fopws')
      mqtt_client.on_message = make_on_message_handler(args[0])
      mqtt_client.on_subscribe = on_subscribe
      
      # Enforce tls certificate checking 
      mqtt_client.tls_set()
      mqtt_client.enable_logger(logger)

      mqtt_client.username_pw_set(mqtt_username, decrypt(mqtt_password))
      mqtt_client.connect(mqtt_url, mqtt_port, 60)

      # Start the MQTT client - loop_start causes the mqtt_client to spawn a background thread which
      #                         handles the mqtt commuications.  The loop_start call thus returns
      #                         control to this thread immediately.

      args[1]['mqtt_client'] = mqtt_client
      logger.info('starting an mqtt thread...')
      #- mqtt_client.loop_forever()
      mqtt_client.loop_start()

      # Camp out forever in order to keep Gunicorn happy
      while True:
          args[0].sleep(10)
          args[0].emit('mqtt thread alive')
      
      """-
      mqtt_client.loop_start()
      emit('response', 'connected as foobar')
      logger.info('started MQTT client')
      return mqtt_client
      """

   except:
      logger.error('Unable to create MQTT client: {} {}'.format(exc_info()[0], exc_info()[1]))

def apply_cmd(repl_state, emit,  cmd):
   #- emit('response', 'hooya')
   #- state['socketio'].emit('response', 'hooya2') # {repl_state['sid']})
   if cmd == 'mqtt_connect':
      emit('response', 'got here')
      repl_state['mqtt_client'] = mqtt_connect(emit, repl_state)
   elif cmd == 'mqtt_subscribe_all':
      mqtt_subscribe_all(repl_state, emit)    

   return 'ok' 

"""-
def start(request, emitter):
   repl_state = {}
   logger.info('starting repl')
   repl_state['start_time'] = time()
   repl_state['up_time'] = up_time
   repl_state['apply'] = apply_cmd
   return repl_state 
""" 
