import os
import string

from nltk.corpus import (gutenberg,
                        wordnet as wn)
from nltk.corpus.reader import NOUN
from nltk.corpus.reader import PlaintextCorpusReader
from nltk.tag import pos_tag
from nltk.tag.simplify import simplify_wsj_tag
from nltk.tokenize import (word_tokenize,
                          wordpunct_tokenize,
                          sent_tokenize)
from tags import DESCRIPTIONS as tag_descriptions


def plural(word):
  if word.endswith('y'):
    return word[:-1] + 'ies'
  elif word[-1] in 'sx' or word[-2:] in ['sh', 'ch']:
    return word + 'es'
  elif word.endswith('an'):
    return word[:-2] + 'en'
  else:
    return word + 's'


def is_punctuation(word):
  return word in string.punctuation or word == '--'


def pos_tag_sentence(sent, simplify_tags=False):
  tagged = pos_tag(sent)
  if simplify_tags:
    tagged = [ (word, simplify_wsj_tag(tag)) for word, tag in tagged ]
  return tagged


class NLTKReader(object):

  ERROR = 0
  WARN = 1
  INFO = 2
  DEBUG = 3

  def __init__(self, input=None, cache_dir='/tmp/nupic_nlp', verbosity=0):
    # Create the cache directory if necessary.
    if not os.path.exists(cache_dir):
      os.mkdir(cache_dir)
    self.cache_dir = cache_dir
    self._verbosity = verbosity
    if input is not None:
      self.input_reader = PlaintextCorpusReader(input, '.*\.txt')
    else:
      self.input_reader = None


  def _log(self, lvl, msg):
    if lvl <= self._verbosity:
      print msg


  def _is_noun(self, word):
    synonyms = len(wn.synsets(word, NOUN))
    self._log(self.DEBUG, 'found %i noun synonyms for %s' % (synonyms, word))
    return synonyms > 0


  def _get_cache_file(self, cache_name):
    return os.path.join(self.cache_dir, cache_name)


  def _write_cache(self, cache_name, data):
    cache_file = self._get_cache_file(cache_name)
    self._log(self.INFO, 'writing cache to %s' % cache_file)
    with open(cache_file, 'w') as f:
      f.write(data)


  def _cache_exists(self, cache_name):
    cache_file = self._get_cache_file(cache_name)
    return os.path.exists(cache_file)


  def _read_cache(self, cache_name):
    cache_file = self._get_cache_file(cache_name)
    self._log(self.INFO, 'reading cache from %s' % cache_file)
    return open(cache_file, 'r').read()


  def _check_text_availability(self, text_name):
    if text_name not in self.available_texts():
      raise Exception('No corpus available named "%s".' % text_name)


  def _get_reader_for(self, text_name):
    if text_name in gutenberg.fileids():
      return gutenberg
    else:
      return self.input_reader


  def available_texts(self):
    available = gutenberg.fileids()
    if self.input_reader is not None:
      available = available + self.input_reader.fileids()
    return available


  def text_report(self):
    print '%40s %10s %10s' % ('text', 'words', 'sentences')
    for txt in self.available_texts():
      word_count = len(self.get_words(txt))
      sent_count = len(self.get_sentences(txt))
      print '%40s %10i %10i' % (txt, word_count, sent_count)


  def get_words_from_text(self, text_name):
    self._check_text_availability(text_name)
    words_with_puncuation = self.get_words(text_name)
    # Strip punctuation and make lower case.
    words = [w.lower()
      for w in words_with_puncuation
      if w not in string.punctuation and len(w) > 3]
    # Remove duplicate nouns.
    words = list(set(words))
    self._log(self.INFO, 'Found %i unique words from %s' % (len(words), text_name))
    return words


  def get_nouns_from_text(self, text_name):
    self._log(self.INFO, '\nGetting nouns from %s' % text_name)
    cache_name = 'nouns_' + text_name
    if self._cache_exists(cache_name):
      nouns = self._read_cache(cache_name).split(',')
    else:
      words = self.get_words_from_text(text_name)
      self._log(self.WARN, 'Noun identification beginning. This might take awhile...')
      self._log(self.INFO, 'Tagging part of speech for %i words...' % len(words))
      tagged_words = pos_tag(words)

      self._log(self.INFO, 'Extracting all non-nouns based on POS tag...')
      nouns = [ word for word, pos in tagged_words if len(word) > 2 and pos == 'NN']
      self._log(self.INFO, '\t%i left' % len(nouns))

      self._log(self.INFO, 'Extracting further non-nouns based on Wordnet synonyms...')
      nouns = [ noun for noun in nouns if self._is_noun(noun) ]
      self._log(self.INFO, '\t%i left' % len(nouns))

      self._write_cache(cache_name, ','.join(nouns))

    self._log(self.INFO, 'Found %i total nouns from %s' \
      % (len(nouns), text_name))
    return nouns


  def get_noun_pairs_from_all_texts(self):
    """Retrieves all nouns from the NLTK corpus of texts."""
    singulars = []
    for text in self.available_texts():
      singulars += self.get_nouns_from_text(text)
    singulars = list(set(singulars))
    return [(singular, plural(singular)) for singular in singulars]


  def get_words(self, text_name):
    self._check_text_availability(text_name)
    return self._get_reader_for(text_name).words(text_name)


  def get_sentences(self, text_name):
    self._check_text_availability(text_name)
    return self._get_reader_for(text_name).sents(text_name)


  def get_tagged_sentences(self, text_name, exclude_punctuation=False, simplify_tags=False):
    for sent in self.get_sentences(text_name):
      if exclude_punctuation:
        sent = [ word for word in sent if not is_punctuation(word) ]
      yield pos_tag_sentence(sent, simplify_tags=simplify_tags)


  def get_parts_of_speech(self, text_name, exclude_punctuation=False, simplify_tags=False):
    self._log(self.INFO, 'Parts of speech extraction beginning. This might take awhile...')
    pos = set()
    for sent in self.get_tagged_sentences(text_name,
                                          exclude_punctuation=exclude_punctuation,
                                          simplify_tags=simplify_tags):
      words, parts = zip(*sent)
      pos.update(parts)
    # String blanks (not sure why there are blanks, but there are sometimes).
    return sorted([ p for p in pos if p is not '' ])


  def get_tag_descriptions(self):
    return tag_descriptions


  def describe_tag(self, tag):
    if tag not in tag_descriptions.keys():
      # Return original tag if we don't know it
      return (tag,tag)
    return tag_descriptions[tag]
