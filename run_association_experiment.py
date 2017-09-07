#!/usr/bin/env python
import os
import sys
import time
from optparse import OptionParser
from nupic_nlp import SDRBuilder, NupicWordClient, AssociationRunner

BMP_WIDTH = 128
BMP_HEIGHT = 128
BMP_LENGTH = BMP_WIDTH * BMP_HEIGHT

if 'CORTICAL_API_KEY' not in os.environ:
  print 'Missing CORTICAL_API_KEY environment variables.'
  print 'You can retrieve these by registering for the CEPT API at '
  print 'http://www.cortical.io/'
  quit(-1)

corticalApiKey = os.environ['CORTICAL_API_KEY']

DEFAULT_MAX_TERMS = '100'
DEFAULT_MIN_sparsity = 2.0 # percent
DEFAULT_PREDICTION_START = '50'
cacheDir = './cache'

parser = OptionParser(usage="%prog input_file [options]")

parser.add_option('-t', '--max-terms',
  default=DEFAULT_MAX_TERMS,
  dest='maxTerms',
  help='Maximum terms to process. Specify "all" for to process all available \
terms.')

parser.add_option('-s', '--min-sparsity',
  default=DEFAULT_MIN_sparsity,
  dest='minSparsity',
  help='Minimum SDR sparsity threshold. Any words processed with sparsity lower \
than this value will be ignored.')

parser.add_option('-p', '--prediction-start',
  default=DEFAULT_PREDICTION_START,
  dest='predictionStart',
  help='Start converting predicted values into words using the CEPT API after \
this many values have been seen.')

parser.add_option('--triples',
  action="store_true", default=False,
  dest='predictTriples',
  help='If specified, assumes word file contains word triples')

parser.add_option("-v", "--verbose",
  action="store_true",
  dest="verbose",
  default=False,
  help="Prints details about errors and API calls.")


def main(*args, **kwargs):
  """ NuPIC NLP main entry point. """
  (options, args) = parser.parse_args()
  if options.maxTerms.lower() == 'all':
    maxTerms = sys.maxint
  else:
    maxTerms = int(options.maxTerms)
  minSparsity = float(options.minSparsity)
  predictionStart = int(options.predictionStart)
  verbosity = 0
  if options.verbose:
    verbosity = 1

  # Create the cache directory if necessary.
  if not os.path.exists(cacheDir):
    os.mkdir(cacheDir)

  builder = SDRBuilder(corticalApiKey, cacheDir,
                        verbosity=verbosity)

  def sizeToThresholds(sdr_size):
      """ scale minThreshold and activationThreshold according to sdr_size """
      factor = float(sdr_size) / (128*128)
      print factor
      return 80*factor, 100*factor

  minThreshold, activationThreshold = sizeToThresholds(BMP_LENGTH)

  if options.predictTriples:
    # Instantiate TP with parameters for Fox demo
    print activationThreshold
    nupic = NupicWordClient(numberOfCols=BMP_LENGTH,
                            minThreshold=minThreshold,
                            activationThreshold=activationThreshold,
                            verbosity=verbosity)
  else:
    nupic = NupicWordClient(numberOfCols=BMP_LENGTH, verbosity=verbosity)

  runner = AssociationRunner(builder, nupic,
                              maxTerms, minSparsity,
                              predictionStart, verbosity=verbosity)

  if len(args) is 0:
    print 'no input file provided!'
    exit(1)
  elif len(args) == 1:
    if options.predictTriples:
      if options.verbose: print "Predicting triples!"
      runner.directAssociationTriples(args[0])
    else:
      runner.directAssociation(args[0])
  else:
    if options.predictTriples:
      print "Please specify exactly one input file containing triples"
    else:
      runner.randomDualAssociation(args[0], args[1])


if __name__ == "__main__":
  main()
  time.sleep(30)
