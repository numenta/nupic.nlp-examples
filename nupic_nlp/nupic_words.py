import numpy
# This is the class correspondingn to the C++ optimized Temporal Pooler (default)
from nupic.research.TP10X2 import TP10X2 as TP


class Client(object):

  def __init__(self,
               numberOfCols=16384, cellsPerColumn=8,
                initialPerm=0.5, connectedPerm=0.5,
                minThreshold=164, newSynapseCount=164,
                permanenceInc=0.1, permanenceDec=0.0,
                activationThreshold=164, 
                pamLength=10):

    self.tp = TP(numberOfCols=numberOfCols, cellsPerColumn=cellsPerColumn,
                initialPerm=initialPerm, connectedPerm=connectedPerm,
                minThreshold=minThreshold, newSynapseCount=newSynapseCount,
                permanenceInc=permanenceInc, permanenceDec=permanenceDec,
                
                # 1/2 of the on bits = (16384 * .02) / 2
                activationThreshold=activationThreshold, 
                globalDecay=0, burnIn=1,
                checkSynapseConsistency=False,
                pamLength=pamLength)


  def feed(self, sdr):
    tp = self.tp
    narr = numpy.array(sdr, dtype="uint32")
    tp.compute(narr, enableLearn = True, computeInfOutput = True)

    predicted_cells = tp.getPredictedState()
    # print predicted_cells.tolist()
    predicted_columns = predicted_cells.max(axis=1)
    # print predicted_columns.tolist()
    # import pdb; pdb.set_trace()
    return predicted_columns.nonzero()[0].tolist()
  
  def printParameters(self):
    """
    Print CLA parameters
    """
    self.tp.printParameters()
  

  def reset(self):
    self.tp.reset()
