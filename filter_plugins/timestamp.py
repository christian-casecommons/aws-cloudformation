from time import time

class FilterModule(object):
  '''Returns the unix epoch'''
  def filters(self):
    return {
        'timestamp': timestamp
    }

def timestamp(source=None):
  return int(time())
