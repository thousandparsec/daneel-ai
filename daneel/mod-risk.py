import logging
import tp.client.cache
from tp.netlib.objects import OrderDescs
from constraint import *
from problem import *

constraints = """adjacent(int,int)*
reinforcements(int)
armies(int,int)
order_move(int,int,int)
order_reinforce(int,int)
order_colonise(int,int)""".split('\n')

rules = """adjacentset @ adjacent(A,B) \ adjacent(A,B) <=> pass
addarmies @ resources(P,1,N,_) ==> armies(P,N)""".split('\n')

def init(cache,rulesystem,connection):
    planets, systems, adjacent = {}, {}, []
    planet_list = []
    
    #two loops because we want to make sure all planet positions are stored first
    for obj in cache.objects.itervalues():
        if obj.subtype == 3:
            planets[obj.parent] = obj.id
            planet_list. append ( obj.id)
    for obj in cache.objects.itervalues():
        if obj.subtype == 2:
            systems[obj.pos] = planets[obj.id]
    for obj in cache.objects.itervalues():
        if obj.subtype == 5:
            adjacent.extend( [(systems[obj.start],systems[obj.end]), (systems[obj.end],systems[obj.start]),])
    
    rulesystem.setConstant("adjacent_planets", adjacent)
    return



def startTurn(cache,store, delta = 0):
    myplanet = selectOwnedPlanet(cache)
    if myplanet is None:
        logging.getLogger("daneel.mod-risk").warning("No owned planets found. We're dead, Jim.")
        return
    v = cache.objects[myplanet]
    store.addConstraint("reinforcements(%i)"%v.resources[0][2])

def endTurn(cache,rulesystem,connection):
    orders = rulesystem.findConstraint("order_move(int,int,int)")
    for order in orders:
        start = int(order.args[0])
        destination = int(order.args[1])
        amount = int(order.args[2])
        logging.getLogger("daneel.mod-risk").debug("Moving %s troops from %s to %s" % (amount,start,destination))
        moveorder = findOrderDesc("Move")
        args = [0, start, -1, moveorder.subtype, 0, [], ([], [(destination, amount)])]
        order = moveorder(*args)
        evt = cache.apply("orders","create after",start,cache.orders[start].head,order)
        if connection != None:
            tp.client.cache.apply(connection,evt,cache)
    orders = rulesystem.findConstraint("order_reinforce(int,int)")
    for order in orders:
        objid = order.args[0]
        amount = order.args[1]
        logging.getLogger("daneel.mod-risk").debug("Reinforcing %s with %s troops" % (objid,amount))
        orderd = findOrderDesc("Reinforce")
        args = [0, objid, -1, orderd.subtype, 0, [], amount, 0]
        order = orderd(*args)
        evt = cache.apply("orders","create after",objid,cache.orders[objid].head,order)
        if connection != None:
            tp.client.cache.apply(connection,evt,cache)
    orders = rulesystem.findConstraint("order_colonise(int,int)")
    planet = selectOwnedPlanet(cache)
    for order in orders:
        objid = order.args[0]
        amount = order.args[1]
        logging.getLogger("daneel.mod-risk").debug("Colonizing %s with %s troops" % (objid,amount))
        orderd = findOrderDesc("Colonize")
        args = [0, planet, -1, orderd.subtype, 0, [], ([], [(objid, amount)])]
        o = orderd(*args)
        evt = cache.apply("orders","create after",planet,cache.orders[planet].head,o)
        if connection != None:
            tp.client.cache.apply(connection,evt,cache)

def findOrderDesc(name):
    name = name.lower()
    for d in OrderDescs().values():
        if d._name.lower() == name:
            return d

def selectOwnedPlanet(cache):
    me = cache.players[0].id
    for (k,v) in cache.objects.items():
        if v.subtype == 3 and v.owner == me:
            return k