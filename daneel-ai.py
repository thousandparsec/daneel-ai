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
import inspect

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

version = (0, 0, 3)
mods = []

if hasattr(sys, "frozen"):
    installpath = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
else:
    installpath = os.path.realpath(os.path.dirname(__file__))

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
    try:
    	connection.setup(host=host, debug=debug)
    except Exception,e: #TODO make the exception more specific
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

    games = connection.games()
    if failed(games):
        print "Getting the game object failed!"
        return

    cache = Cache(Cache.key(host, games[0], username))
    return connection, cache

def getDataDir():
    if hasattr(sys, "frozen"):
        return os.path.join(installpath, "share", "daneel-ai")
    if "site-packages" in daneel.__file__:
        datadir = os.path.join(os.path.dirname(daneel.__file__), "..", "..", "..", "..", "share", "daneel-ai")
    else:
        datadir = os.path.join(os.path.dirname(daneel.__file__), "..")
    return datadir
   


def createRuleSystem(rulesfile,verbosity,cache,connection):
    global mods
    cons,rules = [],[]
    funcs = {}

    rf = open(os.path.join(getDataDir(), 'rules', rulesfile))
    l = stripline(rf.readline())
    while l != "[Modules]":
        l = stripline(rf.readline())
    l = stripline(rf.readline())
    while l != "[Constraints]":
        if l != "":
            m = getattr(__import__("daneel."+l), l)
            print l, m
            mods.append(m)
            try:
                cons.extend(m.constraints)
            except AttributeError:
                pass
            try:
                rules.extend(m.rules)
            except AttributeError:
                pass
            try:
                exec("".join(m.functions),funcs)
            except AttributeError:
                pass
        l = stripline(rf.readline())
    l = stripline(rf.readline())
    while l != "[Rules]":
        if l != "": cons.append(l)
        l = stripline(rf.readline())
    l = stripline(rf.readline())
    while l != "[Functions]":
        if l != "": rules.append(l)
        l = stripline(rf.readline())
    exec("".join(rf.readlines()),funcs)
    funcs['cache'] = cache
    
    if connection != None:
        funcs['connection'] = connection

    return RuleSystem(cons,rules,funcs,verbosity)

def stripline(line):
    if line[0] == "#": return ""
    return line.strip()

def startTurn(cache,store, delta):
    for m in mods:
    	#call startTurn if it exists in m
        if "startTurn" in [x[0] for x in inspect.getmembers(m)]:
            m.startTurn(cache,store, delta)

def endTurn(cache,rulesystem,connection):
    for m in mods:
    	#call endTurn if it exists in m
        if "endTurn" in [x[0] for x in inspect.getmembers(m)]:
            m.endTurn(cache,rulesystem,connection)

def saveGame(cache):
	root_dir = getDataDir()
	save_dir = root_dir + "/states/"
	writeable = checkSaveFolderWriteable(root_dir, save_dir)
	# NB assumes there is enough space to write
	if not writeable:
		logging.getLogger("daneel").error("Cannot save information")
	else:
		cache.file = save_dir + time.time().__str__() + ".gamestate"
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

def init(cache,rulesystem,connection):
    for m in mods:
    	#call init if it exists in m
    	if "init" in [x[0] for x in inspect.getmembers(m)]:
            m.init(cache,rulesystem,connection)
        #this is for optimisation
        if "optimisationValues" in [x[0] for x in inspect.getmembers(m)]:
            m.optimisationValues(optimiseValue)

def pickle(variable, file_name):
	file = open(file_name, 'wb')
	cPickle.dump(variable, file)
	file.close()
	return

def gameLoop(rulesfile,turns=-1,uri='tp://daneel-ai:cannonfodder@localhost/tp',verbosity=0,benchmark=0):
    try:
        level = {0:logging.WARNING,1:logging.INFO,2:logging.DEBUG}[verbosity]
    except KeyError:
        level = 1
    fmt = "%(asctime)s [%(levelname)s] %(name)s:%(message)s"
    logging.basicConfig(level=level,stream=sys.stdout,format=fmt)
    try:
        connection, cache = connect(uri)
    except Exception, e: #TODO Null make the exception more specific
        import traceback
        traceback.print_exc()

        print "Connection failed."
        print e

        return
    
#    state = picklegamestate.GameState(rulesfile,turns,None,None,verbosity)
#    state.pickle("./states/" + time.time().__str__() + ".gamestate")
	
    gameLoopWrapped(rulesfile,turns,connection,cache,verbosity,benchmark)

def gameLoopWrapped(rulesfile,turns,connection,cache,verbosity,benchmark):		
    rulesystem = createRuleSystem(rulesfile,verbosity,cache,connection)
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
        #saveGame(cache)      
        lastturn = cache.objects[0].Informational[0][0]

        startTurn(cache,rulesystem,delta)
        rulesystem.addConstraint("cacheentered")
        endTurn(cache,rulesystem,connection)

        rulesystem.clearStore()
        connection.turnfinished()
        waitfor = connection.time()
        
        logging.getLogger("daneel").info("Awaiting end of turn %s est: (%s s)..." % (lastturn,waitfor.time))
        try:
            while lastturn == connection.get_objects(0)[0].Informational[0][0]:
                waitfor = connection.time()
                time.sleep(max(1, min(10,waitfor.time / 100)))
        except IOError:
            print "Connection lost"
            exit(2)

def gameLoopBenchMark(rulesfile,turns,connection,cache,verbosity):		
    rulesystem = createRuleSystem(rulesfile,verbosity,cache,connection)
    logging.getLogger("daneel").info("Downloading all data")

    init(cache,rulesystem,connection)
    delta = False
    startTurn(cache,rulesystem,delta)
    rulesystem.addConstraint("cacheentered")
    endTurn(cache,rulesystem,None)
    rulesystem.clearStore()
    
    return

optimiseValue = None

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
    parser.add_option("-b", dest="benchmark", default=0,
                      help="Runs the program in benchmarking mode.")
    parser.add_option("-o", dest="optimise", default=0,
                      help="Runs the program in benchmarking mode.")


    (options, args) = parser.parse_args()
    optimiseValue = options.optimise
    gameLoop(options.filename,turns=options.numturns,uri=options.uri,verbosity=options.verbosity,benchmark=options.benchmark)
