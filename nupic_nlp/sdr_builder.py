import math
import os
import sys
import json
import pycept
import retinasdk

BMP_WIDTH = 128
BMP_HEIGHT = 128
BMP_LENGTH = BMP_WIDTH * BMP_HEIGHT


def plural(word):
  if word.endswith('y'):
    return word[:-1] + 'ies'
  elif word[-1] in 'sx' or word[-2:] in ['sh', 'ch']:
    return word + 'es'
  elif word.endswith('an'):
    return word[:-2] + 'en'
  else:
    return word + 's'


def isValid(sdr, min_sparsity):
  return sdr['sparsity'] > min_sparsity


class Builder(object):

  def __init__(self, apiKey, cacheDir, verbosity=0):
    self.cacheDir = cacheDir
    self.corticalClient = retinasdk.FullClient(
      apiKey, apiServer="http://api.cortical.io/rest",
      retinaName="en_associative"
    )



  def termToSdr(self, term):
    """ Create a cache location for each term, where it will either be read in
    from or cached within if we have to go to the CEPT API to get the SDR."""
    cacheFile = os.path.join(self.cacheDir, term + '.json')
    # Get it from the cache if it's there.
    if os.path.exists(cacheFile):
      fingerprint = json.loads(open(cacheFile).read())
    # Get it from CEPT API if it's not cached.
    else:
      result = self.corticalClient.getTerms(
        term=term, getFingerprint=True
      )
      if len(result) is 0:
        # This means the API doesn't know the term.
        fingerprint = {}
        fingerprint['positions'] = []
      else:
        f = result[0].fingerprint
        fingerprint = dict((name, getattr(f, name)) for name in dir(f) if not name.startswith('__'))
      # attach the sparsity for reference
      on = len(fingerprint['positions'])
      sparsity = float(on) / float(BMP_LENGTH) * 100.0
      fingerprint['sparsity'] = sparsity
      # write to cache
      with open(cacheFile, 'w') as f:
        f.write(json.dumps(fingerprint))
    return fingerprint



  def convertBitmapToSdr(self, bitmap):
    positions = bitmap["positions"]
    sdr = []
    if len(positions) is 0:
      nextOn = None
    else:
      nextOn = positions.pop(0)

    for sdrIndex in range(0, BMP_LENGTH):
      if nextOn is None or nextOn != sdrIndex:
        sdr.append(0)
      else:
        sdr.append(1)
        if len(positions) is 0:
          nextOn = None
        else:
          nextOn = positions.pop(0)

    return sdr


  def closestTerm(self, onBits):
    try:
        closest = self.corticalClient.getSimilarTermsForExpression(
          json.dumps({"positions": onBits.tolist()}), getFingerprint=False
        )
    except Exception as e:
      print e
      # CEPT didn't like our SDR, so we show <garbage> in the output
      closest = [{'term': '<garbage>'},]
    if len(closest) is 0:
      return None
    else:
      return closest[0].term
