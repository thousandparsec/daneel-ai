import tp.client.cache
from tp.netlib.objects import OrderDescs
import sys
import logging
import daneel_ai
from constraint import *
from problem import *

debug = 1

constraints = """fleetbuildingturn
productionturn
order_move(int,int)
order_buildfleet(int,tuple,str)
order_produce(int,tuple)
order_colonise(int,int)""".split('\n')

rules = ["turn(X) ==> X % 3 == 0 | productionturn",
        "turn(X) ==> X % 3 != 2 | fleetbuildingturn"]



def startTurn(cache, daneelproblem, delta=0):
    info(daneelproblem)
    variables = {}
    
    func = lambda objects,whoami: myPlanets(objects,whoami)
    func_vars = ['objects', 'whoami']
    myplanets = Rule(store= daneelproblem, 
                name='myplanets', 
                vars=[{'varname': 'whoami', 'type':'variable'}, {'varname': 'objects', 'type':'variable'}], 
                cons=[{'func': func, 'func_vars': func_vars}])
    
    daneelproblem.addVariableRule({myplanets.getName(): myplanets})
   
    func = lambda object: isStar(object)
    func_vars =['objects']    
    stars = Rule(store = daneelproblem,
                 name='stars',
                 vars=[{'varname': 'objects', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}])
    
    daneelproblem.addVariableRule({stars.getName(): stars})

    func = lambda object: isScoutShip(object)
    func_vars =['objects']    
    scouts = Rule(store = daneelproblem,
                 name='scouts',
                 vars=[{'varname': 'objects', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}])
    
    daneelproblem.addVariableRule({scouts.getName(): scouts})
    
    func = lambda object: isColonyShip(object)
    func_vars =['objects']    
    colonyships = Rule(store = daneelproblem,
                 name='colonyships',
                 vars=[{'varname': 'objects', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}])
    
    daneelproblem.addVariableRule({colonyships.getName(): colonyships})
    
    
    # TODO: ORDER SELECTION STILL INCOMPLETE
    
    num_stars = len(stars.getsol())
    if ( num_stars > 10):
        #TODO:
        # order_buildfleet(P,((1,1),),"Scouting"
        pass
    
    for item in myplanets.getsol():
        # TODO:
        #order_produce(P,((7,1),))
        pass
    
    if(debug):
        sys.exit()
    
    
    return
    


def info(problem):
    turn = problem.getVariableRuleSolutions('turn')
    logging.getLogger("TURN").info('The turn is %s', turn.pop())   


def isScoutShip(object):
    if not( isFleet(object)):
        return False
    else:
        try:
            return object['name'] == "Scouting"
        except:
            return False

def isColonyShip(object):
    if not( isFleet(object)):
        return False
    else:
        try:
            return object['name'] == "Colonization"
        except:
            return False

def isUniverse(object):
    try:
        return object['subtype'] == 0
    except:
        return False
    
def isGalaxy(object):
    try:
        return object['subtype'] == 1
    except:
        return False
    
def isStar(object):
    try:
        return object['subtype'] == 2
    except:
        return False
    
def isPlanet(object):
    try:
        return object['subtype'] == 3
    except:
        return False
    
def isFleet(object):
    try:
        return object['subtype'] == 4
    except:
        return False

def isWormhole(object):
    try:
        return object['subtype'] == 5
    except:
        return False

    
def myObject(player_id, object):
    try:
        return player_id == object['owner']
    except:
        return False
    
def myPlanets(object, player_id):
    if not (myObject(player_id, object)):
        return False
    if not (isPlanet(object)):
        return False
    else:
        return True
     
     
def endTurn(cache,rulesystem,connection):
    orders = rulesystem.findConstraint("order_move(int,int)")
    for order in orders:
        objid = int(order.args[0])
        destination = int(order.args[1])
        print "Moving %s to %s" % (objid,cache.objects[destination].pos)
        moveorder = findOrderDesc("Move")
        args = [0, objid, -1, moveorder.subtype, 0, [], destination]
        order = moveorder(*args)
        evt = cache.apply("orders","create after",objid,cache.orders[objid].head,order)
        tp.client.cache.apply(connection,evt,cache)
    orders = rulesystem.findConstraint("order_buildfleet(int,tuple,str)")
    for order in orders:
        objid = order.args[0]
        ships = list(order.args[1])
        name = order.args[2]
        print "Ordering fleet %s of %s" % (name,ships)
        buildorder = findOrderDesc("Build Fleet")
        args = [0, objid, -1, buildorder.subtype, 0, [], [[],ships], (len(name),name)]
        order = buildorder(*args)
        evt = cache.apply("orders","create after",objid,cache.orders[objid].head,order)
        tp.client.cache.apply(connection,evt,cache)
    orders = rulesystem.findConstraint("order_produce(int,tuple)")
    for order in orders:
        objid = order.args[0]
        toproduce = list(order.args[1])
        print "Producing %s" % toproduce
        order = findOrderDesc("Produce")
        args = [0, objid, -1, order.subtype, 0, [], [[],toproduce]]
        o = order(*args)
        evt = cache.apply("orders","create after",objid,cache.orders[objid].head,o)
        tp.client.cache.apply(connection,evt,cache)
    orders = rulesystem.findConstraint("order_colonise(int,tuple)")
    for order in orders:
        objid = order.args[0]
        target = order.args[1]
        print "Colonizing %s" % target
        order = findOrderDesc("Colonise")
        args = [0, objid, -1, order.subtype, 0, [], target]
        o = order(*args)
        evt = cache.apply("orders","create after",objid,cache.orders[objid].head,o)
        tp.client.cache.apply(connection,evt,cache)


def findOrderDesc(name):
    name = name.lower()
    for d in OrderDescs().values():
        if d._name.lower() == name:
            return d
