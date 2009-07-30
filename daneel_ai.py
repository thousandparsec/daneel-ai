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
from pyke import knowledge_engine

version = (0, 0, 3)

def importGameFiles(rulesfile):

	try:
		game_file = getattr(__import__("daneel." + rulesfile), rulesfile)
		return game_file.Game() 
	except:
		raise Exception, "Game rules missing for %s" % rulesfile
	 
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


def saveGame(cache,rulesfile,verbosity):
    root_dir = getDataDir()
    save_dir = os.path.join( root_dir, "states" )
    writeable = checkSaveFolderWriteable(root_dir, save_dir)
    # NB assumes there is enough space to write
    if not writeable:
        logging.getLogger("daneel").error("Cannot save information")
    else:       
        cache.file = os.path.join(save_dir, rulesfile + "_-_" + str(verbosity) +
								   "_-_" + time.time().__str__() + ".gamestate")
        cache.save()


def checkSaveFolderWriteable(root_dir, save_dir):    
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


def gameLoop(rulesfile,turns=-1,uri='tp://daneel-ai:cannonfodder@localhost/tp',verbosity=1,save=0):
    setLoggingLevel(verbosity)
    connection, cache = connect(uri)
    gameLoopWrapped(rulesfile,turns,connection,cache,verbosity,save)

def gameLoopWrapped(rulesfile,turns,connection,cache,verbosity,save):


    daneel_engine = knowledge_engine.engine('rules')        
    game = importGameFiles(rulesfile)
			
    logging.getLogger("daneel").info("Downloading all data")
    cache.update(connection,callback)
    game.init(cache,daneel_engine,connection)

    while turns != 0:
        turns = turns - 1

        logging.getLogger("daneel").info("Downloading updates")
        cache.update(connection,callback)
        
        # store the cache
        if save == '1':
            logging.getLogger("daneel").info("Saving Cache")
            saveGame(cache,rulesfile,verbosity) 
        
        lastturn = cache.objects[0].turn

        game.startTurn(cache,daneel_engine)
        game.endTurn(cache,daneel_engine,connection)
        #if(debug):
         #   time.sleep(10)
            
        connection.turnfinished()
       
        waitfor = connection.time()
        logging.getLogger("daneel").info("Awaiting end of turn %s est: (%s s)..." % (lastturn,waitfor))
        while lastturn == connection.get_objects(0)[0].turn:
            waitfor = connection.time()
            time.sleep( max(1,waitfor / 10))


def gameLoopBenchMark(rulesfile,turns,connection,cache,verbosity):
    setLoggingLevel(verbosity)
    #setLoggingLevel(2)
    daneel_engine = knowledge_engine.engine('rules')
    daneel_engine.reset()        
    logging.getLogger("daneel").info("Running BenchMark")
    game = importGameFiles(rulesfile)
    
    game.init(cache,daneel_engine,connection)
    game.startTurn(cache,daneel_engine)
    game.endTurn(cache,daneel_engine,None)
    return



if __name__ == "__main__":
    parser = OptionParser(version="%prog " + ("%i.%i.%i" % version))
    parser.add_option("-f", "--file", dest="filename", default="rfts",
                      help="read rules from FILENAME [default: %default]")
    parser.add_option("-n", "--numturns", dest="numturns", type="int", default=-1,
                      help="run for NUMTURNS turns [default: unlimited]")
    parser.add_option("-u", "--uri", dest="uri",
                      default='tp://daneel-ai:cannonfodder@localhost/tp',
                      help="Connect to specified URI [default %default]")
    parser.add_option("-v", action="count", dest="verbosity", default=1,
                      help="More verbose output. -vv and -vvv increase output even more.")
    parser.add_option("-s", dest="save", default=0,
                      help="Saves the game for benchmarking.")


    (options, args) = parser.parse_args()
    
    gameLoop(options.filename,turns=options.numturns,uri=options.uri,verbosity=options.verbosity,save=options.save)