from logger import get_sub_logger 
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
