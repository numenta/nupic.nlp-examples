import numpy
from nupic.algorithms.temporal_memory import TemporalMemory as TM


class Client(object):

  def __init__(self,
               numberOfCols=16384,
               cellsPerColumn=8,
               activationThreshold=13,
               minThreshold=10,
               verbosity=0
               ):
    self.tm = TM(
      columnDimensions=(numberOfCols,),
      cellsPerColumn=cellsPerColumn,
      activationThreshold=activationThreshold,
      minThreshold=minThreshold)

    if verbosity > 0:
      print "TM Params:"
      print "columnDimensions: {}".format(self.tm.getColumnDimensions())
      print "cellsPerColumn: {}".format(self.tm.getCellsPerColumn())
      print "activationThreshold: {}".format(self.tm.getActivationThreshold())
      print "minThreshold: {}".format(self.tm.getMinThreshold())
      # print "columnDimensions: {}".format(self.tm.getColumnDimensions())
      # print "columnDimensions: {}".format(self.tm.getColumnDimensions())
      # print "columnDimensions: {}".format(self.tm.getColumnDimensions())
      # print "columnDimensions: {}".format(self.tm.getColumnDimensions())
      # print "columnDimensions: {}".format(self.tm.getColumnDimensions())
      # print "columnDimensions: {}".format(self.tm.getColumnDimensions())

  def feed(self, sdr):
    tm = self.tm
    narr = numpy.array(sdr, dtype="uint32")
    tm.compute(narr, learn=True)
    # This returns the indices of the predictive minicolumns.
    predictiveCells = tm.getPredictiveCells()
    # print predictiveCells
    return numpy.unique(numpy.array(predictiveCells) / tm.getCellsPerColumn())


  def reset(self):
    self.tm.reset()
