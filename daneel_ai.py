#! /usr/bin/python

try:
    import requirements
except ImportError:
    pass

import time
import random
import logging
import sys
import os

from optparse import OptionParser

import tp.client.threads
from tp.netlib.client import url2bits
from tp.netlib import Connection
from tp.netlib import failed, constants, objects
from tp.client.cache import Cache

import daneel
import cPickle
import daneel.dpyke as dengine
import daneel.common as common
import daneel.util as util

version = (0, 0, 3)

def importGameFiles(rulesfile):
    '''
    Import the rulesfile
    '''
    try:
        game_file = getattr(__import__("daneel." + rulesfile), rulesfile)
        return game_file.Game() 
    except:
        raise Exception, "Game rulesfile missing for %s" % rulesfile
     
def callback(mode, state, message="", todownload=None, total=None, amount=None):
    logging.getLogger("daneel").debug("Downloading %s %s Message:%s", mode, state, message)

def connect(uri='tp://daneel-ai:cannonfodder@localhost/tp'):
    debug = False

    host, username, game, password = url2bits(uri)
    print host, username, game, password
    if not game is None:
        username = "%s@%s" % (username, game)

    connection = Connection()

    # Download the entire universe
    if connection.setup(host=host, debug=debug):
        print "Unable to connect to the host."
        return

    if failed(connection.connect("daneel-ai/%i.%i.%i" % version)):
        print "Unable to connect to the host."
        return

    if failed(connection.login(username, password)):
        # Try creating the user..
        print "User did not exist, trying to create user."
        if failed(connection.account(username, password, "", "daneel-ai bot")):
            print "Username / Password incorrect."
            return

        if failed(connection.login(username, password)):
            print "Created username, but still couldn't login :/"
            return

    cache = Cache(Cache.key(host, username))
    return connection, cache

def setLoggingLevel(verbosity, stream=sys.stdout):
    try:
        level = {0:logging.WARNING,1:logging.INFO,2:logging.DEBUG}[verbosity]
    except KeyError:
        level = 1
    fmt = "%(asctime)s [%(levelname)s] %(name)s:%(message)s"
    logging.basicConfig(level=level,stream=sys.stdout,format=fmt)
    return
   
def gameLoop(rulesfile,turns=-1,uri='tp://daneel-ai:cannonfodder@localhost/tp',verbosity=1,save=0,learning=0):
    
    #setup the logger to be used throughout the gameloop
    setLoggingLevel(verbosity)
    
    
    connection, cache = connect(uri)

    # import the required rulesfile
    game = importGameFiles(rulesfile)
    
    #load the knowledge_engine
    daneel_engine = dengine.engine('rules')
    daneel_engine.reset()        
    
    
    # create storage object to store program variables
    parsec = common.ParsecGameStore(rulesfile,daneel_engine,cache,connection,verbosity,
                                    learning,save,0)
            
    logging.getLogger("daneel").info("Downloading all data")
    parsec.cache.update(parsec.connection,callback)
    
    # initialise the knowledge_base once at turn 0
    game.init(parsec)

    # set the state to 0 meaning the game is not over
    state = 0
    # continue the loop until we have an end state
    while state == 0:
        '''
        Main loop for the game
        '''
        
        # slight delay to stop flooding the server
        time.sleep(0.5)
        
        logging.getLogger("daneel").info("Downloading updates")
        
        #reload the cache
        parsec.cache.update(parsec.connection,callback)
        
        # the current turn
        lastturn = parsec.cache.objects[0].turn

        # parse the cache and load facts into the knowledge_base
        game.startTurn(parsec)
        
        # check whether we have won or loss or to continue
        state = game.checkGame(parsec)
        if state == 0:
            # we have not won.. perform moves
            game.endTurn(parsec)
            
            # wait until the turn is over
            parsec.connection.turnfinished()
            waitfor = parsec.connection.time()
            logging.getLogger("daneel").info("Awaiting end of turn %s est: (%s s)..." % (lastturn,waitfor))
            # continually check until it is a new turn
            while lastturn == parsec.connection.get_objects(0)[0].turn:
                waitfor = parsec.connection.time()
                time.sleep( max(1,waitfor / 10))

        else:
            util.learn(parsec, state)
        
    if parsec.learning == '1':
        parsec.saveWeights()
    return state        

     

def gameLoopBenchMark(parsec):
    '''
    Ran when profiling. Mini version of gameLoop()
    The knowlege_base is already loaded when it is unpickled.
    So all that is done is the decision making process.
    '''
    setLoggingLevel(parsec.verbosity)

    logging.getLogger("daneel").info("Running BenchMark")
    game = importGameFiles(parsec.rulesfile)
    
    state = game.checkGame(parsec)
    
    if state == 0:
        game.endTurn(parsec)
    else:
        pass
    
    return state
   



if __name__ == "__main__":
    parser = OptionParser(version="%prog " + ("%i.%i.%i" % version))
    parser.add_option("-f", "--file", dest="filename", default="rfts",
                      help="read rules from FILENAME [default: %default]")
    parser.add_option("-n", "--numturns", dest="numturns", type="int", default=-1,
                      help="run for NUMTURNS turns [default: unlimited]")
    parser.add_option("-u", "--uri", dest="uri",
                      default='tp://daneel_ai:cannonfodder@localhost/tp',
                      help="Connect to specified URI [default %default]")
    parser.add_option("-v", action="count", dest="verbosity", default=1,
                      help="More verbose output. -vv and -vvv increase output even more.")
    parser.add_option("-s", dest="save", default=0,
                      help="Saves the game for benchmarking.")
    parser.add_option("-l", dest="learning", default=0,
                      help="Enable TD learning")


    (options, args) = parser.parse_args()
    
    gameLoop(options.filename,turns=options.numturns,uri=options.uri,verbosity=options.verbosity,
             save=options.save, learning=options.learning)