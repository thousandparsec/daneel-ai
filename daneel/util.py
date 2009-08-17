import cPickle
import os
from time import gmtime, strftime, sleep
import sys
import daneel
from tp.netlib.objects import OrderDescs


def learn(parsec, state=0, learning_rate= 0.05, ylambda = 0.7 ):
    '''
    Implements TD-lambda with no discount factor.
    '''
    # wait till we have enough values
    if len(parsec.td) < 3:
        return
    
    else:
        temp = parsec.td
        # reverse so the newest values are first
        temp.reverse()
        
        new_weights = []
        e = 0
        
        # foreach weight
        # new_weight = weight + learning rate * diff between last 2 states * \
        # the sum of lamda ^ statte - i * the partial derivative of the eval func
        for weight in parsec.weights:
            nw = weight
            i = 0
            try:
                
                nn = temp[i]
                next = temp[i + 1]

                '''
                Check if we have won or loss the game
                Increase / decrease the value if we have won.
                
                '''
                if state == -1:
                   next[0] +=  nn[0]
                if state == 1:
                    next[0] -= nn[0]
                
                diff = nn[0] - next[0]
                total = 0

                for tdnode in temp:
                    try:
                        poww = ylambda ** ((len(parsec.td) - i))
                        deriv = doDerive(tdnode[1], e)
                        total += poww * deriv
                    except:
                        pass
                    i += 1
                nw = nw + learning_rate * diff * total
                logging.getLogger("daneel").debug("Old weight = %s, new_weight = %s" % (weight, nw))
                new_weights.append(nw)
            except:
                pass
    
            e += 1
        
        if new_weights != []:
            parsec.weights = new_weights


def doDerive(nodeTuple, num):
    '''
    only valid for linear functions.
    Need a better solution. FIXME
    '''
    return nodeTuple[num]



def saveGame(parsec):
    '''
    Saves a ParsecGameStore object to a file.
    
    '''
    root_dir = getDataDir()
    save_dir = os.path.join( root_dir, "states" )
    writeable = checkSaveFolderWriteable(root_dir, save_dir)
    # NB assumes there is enough space to write
    if not writeable:
        logging.getLogger("daneel").error("Cannot write to %s" % save_dir)
    else:
        
        # temp values so they can be restored after pickling
        temp_conn = parsec.connection
        temp_cache = parsec.cache
        temp_saving = parsec.saving
        temp_learning = parsec.learning
        
        
        # set the values to ones designed for pickling
        # so that we don't try connecting to a sever that does
        # not exist later!
        parsec.cache = None
        parsec.connection = None
        parsec.saving = False
        parsec.learning = False
        parsec.pickled = True
   
   
        # append the time to the rulesfile name
        # sleep for one second to assure the name is unique
        sleep(1)
        timestr = strftime("%Y%m%d%H%M%S", gmtime())
        filename = parsec.rulesfile + "_" + timestr + ".dat"
        location = os.path.join(save_dir, filename)
        parsec.pickle(parsec, location)
        
        parsec.cache = temp_cache
        parsec.connection = temp_conn       
        parsec.saving = temp_saving
        parsec.learning = temp_learning 
        parsec.pickled = False



def getDataDir():
    
    if hasattr(sys, "frozen"):
        installpath = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
    else:
        installpath = os.path.realpath(os.path.dirname(__file__))
        
    if hasattr(sys, "frozen"):
        return os.path.join(installpath, "share", "daneel-ai")
    if "site-packages" in daneel.__file__:
        datadir = os.path.join(os.path.dirname(daneel.__file__), "..", "..", "..", "..", "share", "daneel-ai")
    else:
        datadir = os.path.join(os.path.dirname(daneel.__file__), "..")
    return datadir

def stripline(line):
    if line[0] == "#": return ""
    return line.strip()


def checkSaveFolderWriteable(root_dir, save_dir):
    '''
    Verify we have write access.
    '''    
    dir_exists = os.access(save_dir, os.F_OK)
    dir_writeable = os.access(save_dir, os.W_OK)
    dir_root_writeable = os.access(root_dir, os.W_OK)
    if dir_exists and dir_writeable:
        return True
    if dir_exists and not dir_writeable:
        return False
    if dir_root_writeable:
        os.mkdir(save_dir)
        return True
    else:
        return False
    
    
    
def findOrderDesc(name):
    '''
    Connect to the server to return the Order description given an order name
    as a string.
    '''
    name = name.lower()
    for d in OrderDescs().values():
        if d._name.lower() == name:
            return d

