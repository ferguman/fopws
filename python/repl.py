from config.config import mqtt_url, mqtt_port, mqtt_username,  mqtt_password
from flask_socketio import emit
from logger import get_sub_logger 
from nacl_fop import decrypt
import paho.mqtt.client as mqtt
from sys import exc_info
from time import time

logger = get_sub_logger('repl')

#- repl_state = {}
#- repl_state['start_time'] = None 

"""-
def background_thread():
    # Example of how to send server generated events to clients.
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')
"""

def start_repl():
    repl_state = {}
    logger.info('starting repl')
    repl_state['start_time'] = time()
    repl_state['apply'] = apply_cmd
    while True:
        socketio.sleep(10)
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'uptime': uptime(repl_state)},
                      namespace='/repl')

def up_time(repl_state):
   return time() - repl_state['start_time']

def make_on_message_handler(repl_state):
   
   def on_message(client, userdata, message):
      msg = 'MQTT: userdata: {}, payload: {}'.format(userdata, message.payload.decode('utf-8'))
      logger.info(msg)
      #TODO - need to send this back through the socket io connection to the listener
      #- repl_state['emit']('response', msg)
      #- repl['emit']('response', 'foobar')
      #- repl_state['socketio'].emit('response', msg, repl_state['sid'])
      #- repl_state['socketio'].emit('response', repl_state['sid'], {'data':msg})
      repl_state['socketio'].emit('response', {'data':msg}, room=repl_state['sid'])

   return on_message 

def on_subscribe(mqtt, userdata, mid, granted_qos):
    msg = 'MQTT Subscribed, data: {}, mid: {}'.format(userdata, mid)
    logger.info(msg)

def mqtt_subscribe_all(repl_state, emit):
   # subscribe to all incoming topics
   repl_state['mqtt_client'].subscribe('#', 2)
   msg = 'subscribing to all MQTT topics'
   emit('response', msg)
   logger.info(msg)

def mqtt_connect(emit, repl_state):
   try:
     
      emit('response', 'connecting to mqtt..')

      mqtt_client = mqtt.Client('foobar')
      mqtt_client.on_message = make_on_message_handler(repl_state)
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

      emit('response', 'connected as foobar')
      logger.info('started MQTT client')
      return mqtt_client

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
