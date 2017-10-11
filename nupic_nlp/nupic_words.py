import numpy

from nupic.algorithms.temporal_memory import TemporalMemory as TM


class Client(object):

  def __init__(self,
               numberOfCols=16384,
               cellsPerColumn=8,
               activationThreshold=60,
               minThreshold=60,
               verbosity=0
               ):
    self.tm = TM(
      columnDimensions=(numberOfCols,),
      cellsPerColumn=cellsPerColumn,
      activationThreshold=activationThreshold,
      minThreshold=minThreshold,
      maxNewSynapseCount=164,
      initialPermanence=0.21,
      connectedPermanence=0.3,
      permanenceIncrement=0.1,
      permanenceDecrement=0.0,
      predictedSegmentDecrement=0.0,
    )

    if verbosity > 0:
      print "TM Params:"
      print "columnDimensions: {}".format(self.tm.getColumnDimensions())
      print "cellsPerColumn: {}".format(self.tm.getCellsPerColumn())
      print "activationThreshold: {}".format(self.tm.getActivationThreshold())
      print "minThreshold: {}".format(self.tm.getMinThreshold())
      print "maxNewSynapseCount {}".format(self.tm.getMaxNewSynapseCount())
      print "initialPermanence {}".format(self.tm.getInitialPermanence())
      print "connectedPermanence {}".format(self.tm.getConnectedPermanence())
      print "permanenceIncrement {}".format(self.tm.getPermanenceIncrement())
      print "permanenceDecrement {}".format(self.tm.getPermanenceDecrement())
      print "predictedSegmentDecrement {}".format(self.tm.getPredictedSegmentDecrement())

  def feed(self, sdr, learn=True):
    tm = self.tm
    narr = numpy.array(sdr, dtype="uint32")
    tm.compute(narr, learn=learn)
    # This returns the indices of the predictive minicolumns.
    predictiveCells = tm.getPredictiveCells()

    return numpy.unique(numpy.array(predictiveCells) / tm.getCellsPerColumn())


  def reset(self):
    self.tm.reset()
