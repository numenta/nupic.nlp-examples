import string
from random import choice
import numpy
import sys

# Max number of bits set in a SDR sent to cortical to avoid HTTP 500 errors
# SDRs denser than this must be randomly subsampled
MAX_BITMAP_SIZE = 1024

BMP_WIDTH = 128
BMP_HEIGHT = 128
BMP_LENGTH = BMP_WIDTH * BMP_HEIGHT



def readWordsFrom(file):
  lines = open(file).read().strip().split('\n')
  return [tuple(line.split(',')) for line in lines]

def stripPunctuation(s):
  return s.translate(string.maketrans("",""), string.punctuation)


class SparsityException(Exception):
  pass


def prompt(question):
  sys.stdout.write(question)
  choice = raw_input().lower()

class AssociationRunner(object):

  def __init__(self, builder, nupic, maxTerms, minSparsity, predictionStart, verbosity=0):
    self.builder = builder
    self.nupic = nupic
    self.maxTerms = maxTerms
    self.minSparsity = minSparsity
    self.predictionStart = predictionStart
    self.verbosity = verbosity
    if verbosity > 0:
      print "Association_Runner parameters:"
      print "predictionStart:",predictionStart
      print "maxTerms:",maxTerms
      print "minSparsity:",minSparsity
    self.random = numpy.random.RandomState()
    self.random.seed(40)


  def associate(self, pairs):
    print 'Prediction output for %i pairs of terms' % len(pairs)
    print '\n#%5s%16s%16s |%20s' % ('COUNT', 'TERM ONE', 'TERM TWO', 'TERM TWO PREDICTION')
    print '--------------------------------------------------------------------'

    for count in range(0, self.maxTerms):
      # Loops over association list until maxTerms is met
      if count >= len(pairs):
        pairs += pairs
      term1 = stripPunctuation(pairs[count][0]).lower()
      term2 = stripPunctuation(pairs[count][1]).lower()
      fetchResult = (count >= self.predictionStart)
      try:
        term2Prediction, predictedWords = self._feedTerm(term1, fetchResult)
        self._feedTerm(term2)
        self.nupic.reset()
      except SparsityException as sparsityErr:
        if self.verbosity > 0:
          print sparsityErr
          print 'skipping pair [%s, %s]' % pairs[count]
        continue
      if term2Prediction:
        print '#%5i%16s%16s |%20s' % (count, term1, term2, term2Prediction)

    return term2Prediction


  def associateTriples(self, triples):
    print 'Prediction output for %i triples of terms' % len(triples)
    print '\n#%5s%16s%16s%16s |%20s' % ('COUNT', 'TERM ONE',
                                    'TERM TWO', 'TERM THREE',
                                    'TERM THREE PREDICTION')
    print ('-----------------------------------------------------------------'
          '------------')
    fetchPredictedWord = True
    learn = True
    for count in range(0, self.maxTerms):
      # Loops over association list until maxTerms is met
      if count >= len(triples):
        triples += triples
      term1 = stripPunctuation(triples[count][0]).lower()
      term2 = stripPunctuation(triples[count][1]).lower()
      term3 = stripPunctuation(triples[count][2]).lower()

      if term1 == "foxes":
        learn = False
        fetchPredictedWord = True
        prompt("But what does the fox eat?? (Press 'return' to see!)\n")
        term3 = ""

      try:
        self._feedTerm(term1, subsample=True, learn=learn)
        term3Prediction, predictedWords = self._feedTerm(
          term2, fetchPredictedWord, subsample=True, learn=learn)
        if term1 != "foxes":
          self._feedTerm(term3, subsample=True, learn=learn)
        self.nupic.reset()
      except SparsityException as sparsityErr:
        if self.verbosity > 0:
          print sparsityErr
          print 'skipping triple',triples[count]
        continue
      print '#%5i%16s%16s%16s |%20s' % (count, term1, term2,
                                        term3, term3Prediction)
      if term1 == "foxes":
        print "\nThey might also eat:",
        for term in predictedWords[1:]:
          if term.score > 100:
            print term.term,
        print


  def directAssociation(self, input_file):
    associations = readWordsFrom(input_file)
    self.associate(associations)


  def directAssociationTriples(self, input_file):
    associations = readWordsFrom(input_file)
    self.associateTriples(associations)


  def randomDualAssociation(self, term1_file, term2_file):
    all_first_terms = open(term1_file).read().strip().split('\n')
    all_second_terms = open(term2_file).read().strip().split('\n')
    associations = []
    for count in range(0, self.maxTerms):
      associations.append((choice(all_first_terms), choice(all_second_terms)))
    self.associate(associations)

  def subsampleSdr(self, rawSdr, pct = 0.75):
    """ Subsample the CEPT SDR (json representation) """
    positions = rawSdr['positions']
    rawSdr['positions'] = self.subsampleSdrBitmap(positions, pct)
    rawSdr['sparsity'] = pct*rawSdr['sparsity']
    return rawSdr

  def subsampleSdrBitmap(self, bitmap, pct=0.75):
    """ Subsample the CEPT bitmap """
    n = len(bitmap)
    ns = (int)(pct*n)   # New length
    newIndices = self.random.permutation(n)[0:ns]
    newIndices.sort()
    newPositions = []
    for i in newIndices:
      newPositions.append(bitmap[i])
    return newPositions


  def _feedTerm(self, term, fetchPrediction=False, subsample=False, learn=True):
    rawSdr = self.builder.termToSdr(term)
    sparsity = rawSdr['sparsity']
    if sparsity > 2.0 and subsample:
      rawSdr = self.subsampleSdr(rawSdr)
    if sparsity < self.minSparsity:
      raise SparsityException('"%s" has a sparsity of %.1f%%, which is below the \
      minimum sparsity threshold of %.1f%%.' % (term, sparsity, self.minSparsity))
    predictedBitmap = self.nupic.feed(rawSdr['positions'], learn)
    outputSparsity = float(len(predictedBitmap)) / BMP_LENGTH * 100.0
    if fetchPrediction:
      if len(predictedBitmap) is 0:
        predictedWord = ' '
        predictedWords = []
      elif len(predictedBitmap) >= MAX_BITMAP_SIZE:
        # The predictedBitmap is too dense, so we subsample
        scaling = float(MAX_BITMAP_SIZE) / (len(predictedBitmap) + 20)
        predictedBitmap = self.subsampleSdrBitmap(predictedBitmap, pct=scaling)
        predictedWord, predictedWords = self.builder.closestTerm(predictedBitmap)
      else:
        predictedWord, predictedWords = self.builder.closestTerm(predictedBitmap)
      return predictedWord, predictedWords
    else:
      return None
