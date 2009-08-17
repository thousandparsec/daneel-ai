import cProfile
import pstats
import os
import logging
import sys
import StringIO
import re
import cPickle
import daneel_ai
from daneel_ai import gameLoopBenchMark
import daneel.dpyke as fixpyke
import daneel.util as util


def getStateDir():
    '''
    Retursn the folder where previous saved gamestates are stored as a string.
    '''
    return os.path.join(util.getDataDir(), "states")

    
def isGameStateFile(file_name):
    '''
    Returns true if the file extension is .dat
    '''
    return re.search('.*dat$', file_name)
    

def unpickle(pickle_location):
    '''
    Unpickle the gamestate
    '''
    file = open(pickle_location, 'rb')
    old = cPickle.load(file)
    file.close()
    return old
    
    
def getPickledStates():
    '''
    Returns a list of all the gamestates in the save golder
    '''
    file_list = os.listdir(getStateDir())
    return filter(isGameStateFile, file_list)



class FakeStdOut(object):
    '''
    class to manipulate the location of stdout and stderr
    So that stdout and or stderr maybe displayed to the screen
    and or written to a file.
    Currently stdout goes to screen and file.
    Stderr only goes to a file.
    '''
    def __init__(self, filename, mode):
        self.file = open(filename, mode)
        self.stderr = sys.stderr
        sys.stderr = self
        
    def __del__(self):
        self.close()
        
    def close(self):    
        if self.stderr  is not None:
            sys.stderr = self.stderr
            self.stderr = None
        if self.file is not None:
            self.file.close()
            self.file = None
    
    def write(self, data):
        self.file.write(data)    
#        self.stderr.write(data)
    
    

if __name__=='__main__':
    
    '''
    For each pickledsave state. Run gameLoopBenchmark in the main program.
    So that specific states can be tested multiple times and benchmarked.
    '''
    list_of_states = getPickledStates()

    for state in list_of_states:
        basename = state.partition('.')
        output = os.path.join(getStateDir() , basename[0]  + ".result")
        profile = os.path.join(getStateDir(), basename[0]  + ".profile")
        parsec = unpickle(os.path.join(getStateDir(), state))
        fixpyke.repairPickle(parsec.daneel_engine)
        try:
            cProfile.runctx('gameLoopBenchMark(parsec)', globals(), locals(), profile)
            file = FakeStdOut(output, 'w')
            p = pstats.Stats(profile,stream=file)
            p.strip_dirs().sort_stats('time').print_stats(100)

            file.close()
            
        except:
            print "Profiling of old gamestate: %s failed " % state
            pass

    
    

        
    
