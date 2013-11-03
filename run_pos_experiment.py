 #!/usr/bin/python

import os
from optparse import OptionParser

from nupic_nlp import NLTK_Reader
from nupic.frameworks.opf.modelfactory import ModelFactory

import run_pos_model_params

parser = OptionParser(usage="%prog [options]")

parser.add_option('-t', '--input-text',
  default=None,
  dest='input_text',
  help='The text to process. List available texts with the -l option.')

parser.add_option('-o', '--output-dir',
  default=None,
  dest='output_dir',
  help='Directory to write result files.')

parser.add_option("-v", "--verbose",
  action="store_true",
  dest="verbose",
  default=False,
  help="Prints moar details.")

parser.add_option("-a", "--anomaly",
  action="store_true",
  dest="anomaly",
  default=False,
  help="Get anomaly scores instead of predictions.")

parser.add_option("-n", "--interactive",
  action="store_true",
  dest="interactive",
  default=False,
  help="Opens up for user input after reading the specified.")

parser.add_option("-f", "--full-tagging",
  action="store_true",
  dest="full_tagging",
  default=False,
  help="Uses all available part of speech tagging. Otherwise, simplified NLTK \
tagging is used.")

parser.add_option("-i", "--text-info",
  action="store_true",
  dest="text_info",
  default=False,
  help="Prints a report on available texts.")

parser.add_option("-l", "--list-texts",
  action="store_true",
  dest="list_texts",
  default=False,
  help="Prints a report on available texts.")

parser.add_option("-p", "--pos-report",
  action="store_true",
  dest="pos_report",
  default=False,
  help="Prints all the parts of speech found within the specified text instead \
of processing the text.")


def report(output):
  print '%15s %20s %20s' % tuple(output)


def run_pos_experiment(model, reader, target_text, simple_tags, anomaly, output_file=None):
  last_prediction = ('','')
  for sentence in reader.get_tagged_sentences(target_text, simplify_tags=simple_tags):
    for tag in sentence:
      word = tag[0]
      pos = tag[1]
      model_input = { 'pos': pos }
      result = model.run(model_input)
      if anomaly:
        anomalyScore = result.inferences['anomalyScore']
        if output_file is not None:
          output_file.write('%10s%10s%20f\n' % (word, pos, anomalyScore))
        print '%15s %20s %20f' % (word, reader.describe_tag(pos)[0], anomalyScore)
      else:
        line_out = (word, pos, last_prediction[0])
        if output_file is not None:
          output_file.write('%10s%10s%20s\n' % line_out)
        report((word, reader.describe_tag(pos)[0], last_prediction[1]))
        best_prediciton = result.inferences['multiStepBestPredictions'][1]
        last_prediction = (best_prediciton, reader.describe_tag(best_prediciton)[0])


def process_sentence_for_anomolies(raw_sentence, model, reader, simple_tags):
  sentence = reader.pos_tag_sentence(raw_sentence.split(' '), simple_tags)
  for tag in sentence:
    word = tag[0]
    pos = tag[1]
    model_input = { 'pos': pos }
    result = model.run(model_input)
    anomalyScore = result.inferences['anomalyScore']
    print '%15s %20s %20f' % (word, reader.describe_tag(pos)[0], anomalyScore)


def main(*args, **kwargs):
  """POS Experiment main entry point."""

  (options, args) = parser.parse_args()
  verbosity = NLTK_Reader.WARN
  if options.verbose:
    verbosity = NLTK_Reader.DEBUG

  reader = NLTK_Reader(
    input='./resources/text',
    cache_dir='./cache/text', verbosity=verbosity
  )

  simple_tags = not options.full_tagging

  if options.text_info:
    reader.text_report()
  if options.list_texts:
    print 'Available texts:'
    for t in reader.available_texts():
      print '\t%s' % t

  if options.input_text:
    target_text = options.input_text
  else:
    target_text = None

  if target_text is not None:
    if options.pos_report:
      print 'Parts of Speech found in %s:' % target_text
      for pos in reader.get_parts_of_speech(target_text, simplify_tags=simple_tags):
        tag_description = reader.describe_tag(pos)
        print '\t%6s  %s (%s)' % (pos, tag_description[0], tag_description[1])
    else:
      output_dir = options.output_dir

      model = ModelFactory.create(run_pos_model_params.MODEL_PARAMS)
      model.enableInference({'predictedField': 'pos'})

      if output_dir:
        if not os.path.exists(output_dir):
          os.mkdir(output_dir)
        output_file_path = os.path.join(output_dir, 'pos_out_' + target_text)
        # Clear the output file with a header.
        with open(output_file_path, 'w') as output_file:
          output_file.write('%10s%10s%20s\n' % ('input', 'pos', 'predicted_pos'))
        # Append each result to output file.
        with open(output_file_path, 'a') as output_file:
          run_pos_experiment(model, reader, target_text, simple_tags, options.anomaly, output_file)
      else:
        run_pos_experiment(model, reader, target_text, simple_tags, options.anomaly)

      if options.interactive:
        if options.anomaly:
          while True:
            input_sentence = raw_input('input sentence --> ')
            process_sentence_for_anomolies(input_sentence, model, reader, simple_tags)
        else:
          while True:
            input_word = raw_input('input word --> ')
            process_word


if __name__ == "__main__":
  main()

