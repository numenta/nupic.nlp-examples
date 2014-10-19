import math
import os
import sys
import json
import pycept


def plural(word):
  if word.endswith('y'):
    return word[:-1] + 'ies'
  elif word[-1] in 'sx' or word[-2:] in ['sh', 'ch']:
    return word + 'es'
  elif word.endswith('an'):
    return word[:-2] + 'en'
  else:
    return word + 's'


def is_valid(sdr, min_sparsity):
  return sdr['sparsity'] > min_sparsity


class Builder(object):

  def __init__(self, cept_app_key, cache_dir, retina='eng_gen', verbosity=0):
    self.cept_client = pycept.Cept(cept_app_key, retina=retina, verbosity=verbosity)
    self.cache_dir = cache_dir


  def term_to_sdr(self, term):
    """ Create a cache location for each term, where it will either be read in 
    from or cached within if we have to go to the CEPT API to get the SDR."""
    cache_file = os.path.join(self.cache_dir, term + '.json')
    # Get it from the cache if it's there.
    if os.path.exists(cache_file):
      cached_sdr = json.loads(open(cache_file).read())
    # Get it from CEPT API if it's not cached.
    else:
      cached_sdr = self.cept_client.getBitmap(term)
      if 'sparsity' not in cached_sdr:
        # attach the sparsity for reference
        total = float(cached_sdr['width']) * float(cached_sdr['height'])
        on = len(cached_sdr['positions'])
        sparsity = round((on / total) * 100)
        cached_sdr['sparsity'] = sparsity
      # write to cache
      with open(cache_file, 'w') as f:
        f.write(json.dumps(cached_sdr))
    return cached_sdr



  def convert_bitmap_to_sdr(self, bitmap):
    sdr_string = self.cept_client._bitmapToSdr(bitmap)
    return [int(bit) for bit in sdr_string]



  def closest_term(self, onBits):
    try:
        closest = self.cept_client.bitmapToTerms(onBits)
    except Exception as e:
        # CEPT didn't like our SDR, so we show <garbage> in the output
        closest = [{'term': '<garbage>'},]
    if len(closest) is 0:
      return None
    else:
      return closest[0]['term']
