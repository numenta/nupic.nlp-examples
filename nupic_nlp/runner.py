import string
from random import choice
import numpy
import sys

def read_words_from(file):
  lines = open(file).read().strip().split('\n')
  return [tuple(line.split(',')) for line in lines]

def strip_punctuation(s):
  return s.translate(string.maketrans("",""), string.punctuation)


class Sparsity_Exception(Exception):
  pass


def prompt(question):
  sys.stdout.write(question)
  choice = raw_input().lower()

class Association_Runner(object):

  def __init__(self, builder, nupic, max_terms, min_sparsity, prediction_start, verbosity=0):
    self.builder = builder
    self.nupic = nupic
    self.max_terms = max_terms
    self.min_sparsity = min_sparsity
    self.prediction_start = prediction_start
    self.verbosity = verbosity
    if verbosity > 0:
      print "Association_Runner parameters:"
      print "prediction_start:",prediction_start
      print "max_terms:",max_terms
      print "min_sparsity:",min_sparsity
      print
      print
    self.random = numpy.random.RandomState()
    self.random.seed(40)


  def associate(self, pairs):
    print 'Prediction output for %i pairs of terms' % len(pairs)
    print '\n#%5s%16s%16s |%20s' % ('COUNT', 'TERM ONE', 'TERM TWO', 'TERM TWO PREDICTION')
    print '--------------------------------------------------------------------'

    for count in range(0, self.max_terms):
      # Loops over association list until max_terms is met
      if count >= len(pairs):
        pairs += pairs
      term1 = strip_punctuation(pairs[count][0]).lower()
      term2 = strip_punctuation(pairs[count][1]).lower()
      fetch_result = (count >= self.prediction_start)
      try:
        term2_prediction = self._feed_term(term1, fetch_result)
        self._feed_term(term2)
        self.nupic.reset()
      except Sparsity_Exception as sparsity_err:
        if self.verbosity > 0:
          print sparsity_err
          print 'skipping pair [%s, %s]' % pairs[count]
        continue
      if term2_prediction:
        print '#%5i%16s%16s |%20s' % (count, term1, term2, term2_prediction)
    
    return term2_prediction


  def associate_triples(self, triples):
    print 'Prediction output for %i triples of terms' % len(triples)
    print '\n#%5s%16s%16s%16s |%20s' % ('COUNT', 'TERM ONE',
                                    'TERM TWO', 'TERM THREE',
                                    'TERM THREE PREDICTION')
    print ('-----------------------------------------------------------------'
          '------------')
    for count in range(0, self.max_terms):
      # Loops over association list until max_terms is met
      if count >= len(triples):
        triples += triples
      term1 = strip_punctuation(triples[count][0]).lower()
      term2 = strip_punctuation(triples[count][1]).lower()
      term3 = strip_punctuation(triples[count][2]).lower()
      fetch_result = (count >= self.prediction_start)
      if term1 == "fox":
        print
        prompt("But what does the fox eat?? (Press 'return' to see!)\n")
      try:
        term2_prediction = self._feed_term(term1, fetch_result, subsample=True)
        term3_prediction = self._feed_term(term2, fetch_result, subsample=True)
        self._feed_term(term3, subsample=True)
        self.nupic.reset()
      except Sparsity_Exception as sparsity_err:
        if self.verbosity > 0:
          print sparsity_err
          print 'skipping triple',triples[count]
        continue
      if term3_prediction:
        print '#%5i%16s%16s%16s |%20s' % (count, term1, term2,
                                          term3, term3_prediction)
    
    return term2_prediction


  def direct_association(self, input_file):
    associations = read_words_from(input_file)
    self.associate(associations)


  def direct_association_triples(self, input_file):
    associations = read_words_from(input_file)
    self.associate_triples(associations)


  def random_dual_association(self, term1_file, term2_file):
    all_first_terms = open(term1_file).read().strip().split('\n')
    all_second_terms = open(term2_file).read().strip().split('\n')
    associations = []
    for count in range(0, self.max_terms):
      associations.append((choice(all_first_terms), choice(all_second_terms)))
    self.associate(associations)
    
  def subsample_sdr(self, raw_sdr, pct = 0.75):
    """
    Subsample the CEPT SDR and return a new one. This is a hack to achieve
    proper sparsification. A better mechanism would be to run inputs through
    an SP before sending on to the TP.
    """
    positions = raw_sdr['positions']
    n = len(positions)
    ns = (int)(pct*n)   # New length
    newIndices = self.random.permutation(n)[0:ns]
    newIndices.sort()
    newPositions = []
    for i in newIndices:
      newPositions.append(positions[i])
    raw_sdr['positions'] = newPositions
    raw_sdr['sparsity'] = pct*raw_sdr['sparsity']
    return raw_sdr


  def _feed_term(self, term, fetch_word_from_sdr=False, subsample=False):
    raw_sdr = self.builder.term_to_sdr(term)
    sparsity = raw_sdr['sparsity']
    if sparsity > 2.0 and subsample:
      raw_sdr = self.subsample_sdr(raw_sdr)
    if sparsity < self.min_sparsity:
      raise Sparsity_Exception('"%s" has a sparsity of %.1f%%, which is below the \
minimum sparsity threshold of %.1f%%.' % (term, sparsity, self.min_sparsity))
    sdr_array = self.builder.convert_bitmap_to_sdr(raw_sdr)
    predicted_bitmap = self.nupic.feed(sdr_array)
    output_sparsity = float(len(predicted_bitmap)) / (float(raw_sdr['width']) * float(raw_sdr['height'])) * 100.0
    # print 'Sparsity %s:prediction ==> %.2f%%: %.2f%%' % (term, raw_sdr['sparsity'], output_sparsity)
    if fetch_word_from_sdr:
      if len(predicted_bitmap) is 0:
        predicted_word = ' '
      else:
        predicted_word = self.builder.closest_term(predicted_bitmap)
      return predicted_word
    else:
      return None
