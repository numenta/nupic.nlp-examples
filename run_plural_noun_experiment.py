#!/usr/bin/env python
import os
import sys
from optparse import OptionParser
from nupic_nlp import (NLTK_Reader, 
                       SDR_Builder, 
                       Nupic_Word_Client, 
                       Association_Runner)


if 'CEPT_APP_KEY' not in os.environ:
  print 'Missing CEPT_APP_KEY environment variables.'
  print 'You can retrieve these by registering for the CEPT API at '
  print 'https://cept.3scale.net/'
  quit(-1)

cept_app_key = os.environ['CEPT_APP_KEY']

DEFAULT_MAX_TERMS = '100'
DEFAULT_MIN_sparsity = 0.0 # percent
DEFAULT_PREDICTION_START = '50'
cache_dir = './cache'

parser = OptionParser(usage="%prog input_file [options]")

parser.add_option('-t', '--max-terms',
  default=DEFAULT_MAX_TERMS,
  dest='max_terms',
  help='Maximum terms to process. Specify "all" for to process all available \
terms.')

parser.add_option('-s', '--min-sparsity',
  default=DEFAULT_MIN_sparsity,
  dest='min_sparsity',
  help='Minimum SDR sparsity threshold. Any words processed with sparsity lower \
than this value will be ignored.')

parser.add_option('-p', '--prediction-start',
  default=DEFAULT_PREDICTION_START,
  dest='prediction_start',
  help='Start converting predicted values into words using the CEPT API after \
this many values have been seen.')

parser.add_option("-v", "--verbose",
  action="store_true",
  dest="verbose",
  default=False,
  help="Prints details about errors and API calls.")


def main(*args, **kwargs):
  """ NuPIC NLP main entry point. """
  (options, args) = parser.parse_args()
  if options.max_terms.lower() == 'all':
    max_terms = sys.maxint
  else:
    max_terms = int(options.max_terms)
  min_sparsity = float(options.min_sparsity)
  prediction_start = int(options.prediction_start)
  verbosity = 0
  if options.verbose:
    verbosity = 5

  # Create the cache directory if necessary.
  if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)

  reader = NLTK_Reader(os.path.join(cache_dir, 'text'), verbosity=verbosity)
  builder = SDR_Builder(cept_app_key, cache_dir, verbosity=verbosity)
  nupic = Nupic_Word_Client()
  runner = Association_Runner(builder, nupic, max_terms, min_sparsity, prediction_start, verbosity=verbosity)

  noun_pairs = reader.get_noun_pairs_from_all_texts()[:max_terms]
  
  runner.associate(noun_pairs)


if __name__ == "__main__":
  main()
