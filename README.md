# NuPIC NLP Experiments

This repo contains my Natural Language Processing (NLP) experiments with [NuPIC](http://numenta.org/nupic.html). Some of them are using CEPT word SDRs as input into the NuPIC temporal pooler, bypassing the spacial pooler. Others are simply using the Python Natural Language Tool Kit (NLTK) and parts of speech tagging.

## Requirements

For some experiments, you'll need an app ID and app key from [CEPT](https://cept.3scale.net/) for the usage of their API to get word SDRs and decode SDRs back into words.

You'll also need 35MB (or more depending on what individual experiments you run) of space to store the text corpus from the NLTK and SDRs from CEPT.

## Installation

    pip install -r requirements.txt

### NLTK Download

Before you have the NLTK text corpus available for local processing, you need to download it. See [Installing NLTK Data](http://nltk.org/data.html) for details, but here is the gist:

    >$ python
    >>> import nltk
    >>> nltk.download()

This will bring up a GUI window for you to choose what texts to download. Choose them all and proceed. This will take a few minutes. The NLTK corpus contains somewhere around 6,300 nouns to process, which means over 12K API calls to Cortical for SDRs. The results of each call are cached in the `./cache` directory, so subsequent runs will be much faster, but if you want to run it all in one go, I would suggest you run it overnight and specify `--max-terms=all`.

### Environment

Set up the following environment variable to contain your Cortical.IO API key:

    export CORTICAL_API_KEY=<your_key>

## Caching

All word SDRs from CEPT are cached by default within a `./cache` directory for easy access later, so the CEPT API is not burdened with repeat calls, and script run times don't get overwhelming. You delete this entire directory, or individually cached files within this directory. Additionally, all of the nouns within the NLTK texts are also cached within `/.cache/texts` so the NLTK texts to not need to be reaccessed.

## Experiments

### Word Association

The `run_association_experiment.py` script is a generic script to read input files with word associations and pass them into NuPIC one after the other in an attempt to see if NuPIC will properly associate the semantics encoded with their SDRs.

#### Usage

    ./run_association_experiment.py [input file(s)] [options]

If one input file is specified, it's assumed that there is a hard-coded association on each line of the file, in this format:

    term-a1,term-b1
    term-a2,term-b2
    <etc>

See an example in `resources/animal_food.csv`.

If two input files are specified, a it's assumed that each file has a topical grouping, and associations will be randomly passed into NuPIC from each file. For example, take a look at `resources/animals.txt` and `resources/vegetables.txt`.

    ./run_association_experiment.py resources/animals.txt resources/vegetables.txt -p 100 -t 1000

In the example above, a random term from the animals text is associated with another random term in the vegetables text, and this pair is passed into NuPIC 1000 times. NuPIC's predicted SDRs are passed back into the CEPT API and printed to the screen after 100 iterations. (See options below for details on the `-p` and `-t` options.)

Here is an example of the output you'll get from running the above command:

    $ ./run_association_experiment.py resources/animals.txt resources/vegetables.txt -p 100 -t 1000
    Prediction output for 1000 pairs of terms

    #COUNT        TERM ONE        TERM TWO | TERM TWO PREDICTION
    --------------------------------------------------------------------
    #  100          salmon          endive |              lentil
    #  101       crocodile          borage |
    #  102            wolf        turmeric |            amaranth
    #  103         termite       chickweed |
    #  104           quail            poke |
    #  105      woodpecker         shallot |
    #  106         echidna           caper |              tomato
    #  107         panther            guar |
    #  108             ape       tomatillo |       chrysanthemum
    #  109             bee         cabbage |
    #  110        seahorse          sorrel |
    #  111           camel       tomatillo |          lemongrass
    #  112             rat          chives |
    #  113            crab             yam |              turnip

If the word association is understood by NuPIC, the predictions should be within the same topical category of the second file. NuPIC should even predict words that are not within the original term listing.

##### Options

    --verbose
    -v

Prints details about CEPT API calls and minimum sparsity errors.

    --max-terms=<int>
    -t <int>

How many total terms to run. Stops after reaching this limit. If `all` is specified instead of an integer value, it will run indefinitely.

    --min-sparsity=<float>
    -s <float>

Required SDR sparsity, in percent, for terms to be included. This omits uncommon words from the process. The lower the sparsity, the less words get processed. CEPT will return anywhere from 1.0% to 5.0% sparse representations. The default for this value is 0.0%.

    --prediction-start=<int>
    -p <int>

When to start sending the predicted SDRs from NuPIC back to the CEPT API to translate back into English words. This adds overhead because of the HTTP calls, and initial results will probably be bad. So setting this a bit into your term list is a good idea if you want to time-box the process.

### Parts of Speech

This script does not use CEPT. It parses the input text(s) specified inside the script and breaks each sentence into POS (Parts of Speech) tags. These tags are fed into NuPIC using a [category encoder](https://github.com/numenta/nupic/wiki/Encoders), and each next POS is predicted. Output is written to the console as well as an output file in the output directory specified by `--output-dir`.

#### Usage

    Usage: run_pos_experiment.py [options]

    Options:
      -h, --help            show this help message and exit
      -t INPUT_TEXT, --input-text=INPUT_TEXT
                            The text to process. List available texts with the -l
                            option.
      -o OUTPUT_DIR, --output-dir=OUTPUT_DIR
                            Directory to write result files.
      -v, --verbose         Prints moar details.
      -f, --full-tagging    Uses all available part of speech tagging. Otherwise,
                            simplified NLTK tagging is used.
      -i, --text-info       Prints a report on available texts.
      -l, --list-texts      Prints a report on available texts.
      -p, --pos-report      Prints all the parts of speech found within the
                            specified text instead of processing the text.

#### Example Output

Here is some example console output for Thor's Hammer:

    ./run_pos_experiment.py -t 06_how_thor_got_the_hammer.txt

Partial output:

       WORD                  POS        PREDICTED POS
    -------------------------------------------------
        The           determiner              pronoun
        fly               adverb                 noun
        bit                 noun          proper noun
         me              pronoun                    .
         so               adverb                 noun
       hard               adverb          proper noun
       that          preposition          proper noun
          I              pronoun           determiner
        had           past tense                 noun
         to          the word to          preposition
       stop                 verb                 verb
    blowing                 noun               adverb
          .                    .                    .

As you can see from this sample output, there are problems with NLTK's POS tagging. For example, `bit` is mis-categorized as a noun, when it is used as a past-tense verb. When the input is incorrect, it is harder for NuPIC to predict correctly. You might also note, however, that NuPIC does predict the end of the sentence correctly.

Grammar trees are difficult to predict, even for humans. At any point in the tree, the sentence could branch into multiple directions. Turning this experiment into an anomaly detection problem could provide more valuable results.

## Texts and Terms

All the nouns processed from this corpus of text by the `run_plural_noun_experiment.py` experiment are extracted using NLTK's `pos_tag` function, looking for words tagged with `NN`. Resulting terms seem to be sometimes mis-categorized, so they are also passed through Wordnet and confirmed to be nouns before sent to CEPT for SDR conversion.

## Things to try:

    ./run_association_experiment.py resources/animals.txt resources/vegetables.txt -p 0 -t 1000

Randomly chooses one term from the animal list, and one from the veggie list. Sends that pair through NuPIC, printing NUPIC's prediction for the second term. Should generally choose plant-based objects for the second term after some training.

    ./run_association_experiment.py resources/associations/x-in-y.csv -p 0 -t 300

Reads an input file of country --> capital associations, and passes them into NuPIC in the same way. Doesn't predict very well until it's seen the entire list once, then it is pretty decent.

## What Does The Fox Eat?

The Fox demo was shown during the Fall NuPIC hackathon in SF. The video of that
is here:  http://numenta.org/blog/2013/11/06/2013-fall-hackathon-outcome.html#fox

The fox demo uses the word SDR association framework defined in nupic_nlp to associate
three word phrases, teaching it sentences like "elephants eat leaves", "dogs
like sleep", and "cows eat grass". After some training, we ask NuPIC, "What does
the fox eat?"  Up to this point the CLA had never seen the word fox or anything
about what they eat. In order to solve this task, the CLA has to solve a number
of problems:

1) It has to semantically associate the word fox with other similar words it
has been trained on.  This is achieved using the CEPT SDR representations.

2) It has to learn a primitive three word grammar.

3) It has to learn and predict high order sequences. When processing the verb it
has to remember the noun as well. Both noun1 and verb1 are required to predict
noun2 correctly.

4) It has to predict a word that is semantically correct based on the past
sequence. It has to predict food if the verb is "eat". It has to predict the
right type of food based on the animal that is eating.

So what does the fox eat? Find out the answer by watching the video or running
the demo!

To run the Fox demo, type in:

    ./run_association_experiment.py --triples -p 1 -t 38 resources/associations/foxeat.csv

You should start seeing output that looks like this:

Prediction output for 37 triples of terms

  COUNT        TERM ONE        TERM TWO      TERM THREE |TERM THREE PREDICTION
  -----------------------------------------------------------------------------
      1             cow             eat           grain |               flies
      2        elephant             eat          leaves |               grain
      3            goat             eat           grass |              leaves
      4            wolf             eat          rabbit |              leaves
      5             cat           likes            ball |
      6        elephant           likes           water |                ball
      7           sheep             eat           grass |              leaves
      8             cat             eat          salmon |               grass
      9            wolf             eat            mice |              rabbit

The above is the training set. "TERM THREE PREDICTION" is the prediction given
by the CLA after seeing the first two words. It then sees the actual third term
and adjusts it's connections. For example, in row 6, when it first sees
"elephant likes" it predicts "ball" because that is the only thing it knows that
animals like. It knows enough to not predict flies, grain, etc. but doesn't yet
know that elephants like water.

After 35 training phrases you will see:

    But what does the fox eat?? (Press 'return' to see!)

Press return. The right most word will contain the prediction!

# Next steps for Fox demo

This demo was put together very quickly for the hackathon. There are many
improvements to be made. A couple of suggestions are here:

1) The CEPT API returns SDR's that are at varying levels of sparsity. The
current demo gets around this problem by randomly sparsifying the CEPT SDR's. A
better approach would be to run the CEPT SDR's through a properly configured
spatial pooler followed by a temporal pooler. This is likely to give more robust
results. It will also run faster as we may be able to use a much smaller TP than
is currently used.

2) The current training set was created in a rush for the hackathon. It is
extremely small and performance is brittle. A more comprehensive training set
might make the system a lot more robust.
