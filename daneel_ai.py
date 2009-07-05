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
from daneel.rulesystem import RuleSystem, BoundConstraint
import picklegamestate
import cPickle
from constraint import *
from problem import *

version = (0, 0, 3)
mods = []
debug = 1

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


def startTurn(cache,store, delta):
    for m in store.mods:
        try:
             m.startTurn(cache,store, delta)
        except AttributeError:
            pass
           
    return list

def endTurn(cache,rulesystem,connection):
    for m in rulesystem.mods:
        try:
            m.endTurn(cache,rulesystem,connection)
        except AttributeError:
            pass

def init(cache,rulesystem,connection):
    for m in rulesystem.mods:
        try:
            m.init(cache,rulesystem,connection)
        except AttributeError:
            pass

def gameLoop(rulesfile,turns=-1,uri='tp://daneel-ai:cannonfodder@localhost/tp',verbosity=1,save=0):
    setLoggingLevel(verbosity)
    connection, cache = connect(uri)
    gameLoopWrapped(rulesfile,turns,connection,cache,verbosity,save)

def gameLoopWrapped(rulesfile,turns,connection,cache,verbosity,save):
			
    rulesystem = DaneelProblem(rulesfile,verbosity)
    logging.getLogger("daneel").info("Downloading all data")
    cache.update(connection,callback)
#    state = picklegamestate.GameState(rulesfile,turns,None,cache,verbosity)
 #   state.pickle("./states/" + time.time().__str__() + ".gamestate")

    init(cache,rulesystem,connection)
    
    delta = True
    while turns != 0:
        turns = turns - 1
        logging.getLogger("daneel").info("Downloading updates")
        cache.update(connection,callback)
        # store the cache
        if save == '1':
            print 'saving'
            saveGame(cache,rulesfile,verbosity) 
        
        lastturn = cache.objects[0].turn

        startTurn(cache,rulesystem,delta)
        rulesystem.addConstraint("cacheentered")
        endTurn(cache,rulesystem,connection)
        rulesystem.clearStore(delta)

        if(debug):
            time.sleep(10)
            
        connection.turnfinished()
       
        waitfor = connection.time()
        logging.getLogger("daneel").info("Awaiting end of turn %s est: (%s s)..." % (lastturn,waitfor))
        while lastturn == connection.get_objects(0)[0].turn:
            waitfor = connection.time()
            time.sleep( max(1,waitfor / 10))

def gameLoopBenchMark(rulesfile,turns,connection,cache,verbosity):
    setLoggingLevel(verbosity)   
    problem = DaneelProblem(rulesfile,verbosity)
    logging.getLogger("daneel").info("Running BenchMark")
    init(cache,problem,connection)
    
    delta = False
    startTurn(cache,problem,delta)
    
    if(debug):
        sys.exit()
        
    endTurn(cache,rulesystem,None)
    rulesystem.clearStore(delta)    
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
