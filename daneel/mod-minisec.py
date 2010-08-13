'''
@author: Damjan 'Null' Kosir
'''
import logging
import tp.client.cache
from tp.netlib.objects import OrderDescs
import extra.objectutils
import helper
import random

rulesystem = None

constraints = """order_no_operation(int,int)
order_move(int,int,int,int)
order_build_fleet(int,list,str)
order_colonise(int)
order_split_fleet(int,list)
order_merge_fleet(int)
order_none(int)""".split('\n')

def endTurn(cache2, rulesystem2, connection):
    global rulesystem
    global cache
    #update global stuff
    rulesystem = rulesystem2
    cache = cache2
    helper.rulesystem = rulesystem
    helper.cache = cache
    
    AICode()
    executeOrdersNoOperation(cache, connection)
    executeOrdersMove(cache, connection)
    executeOrdersBuildFleet(cache, connection)
    executeOrdersColonise(cache, connection)
    executeOrdersSplitFleet(cache, connection)
    executeOrdersMergeFleet(cache, connection)

def orderNoOperation(id, wait):
    '''
    Object does nothing for a given number of turns
    id is for the object the order is for
     Arg name: wait    Arg type: Time (code:1)    Arg desc: The number of turns to wait
    '''
    global rulesystem
    rulesystem.addConstraint("order_no_operation(" + str(id) + ", " + str(wait) + ")")
    return

def orderMove(id, pos):
    '''
    Move to a given position absolute in space
    id is for the object the order is for
     Arg name: pos    Arg type: Absolute Space Coordinates (code:0)    Arg desc: The position in space to move to
    '''
    global rulesystem
    rulesystem.addConstraint("order_move(" + str(id) + ", " + str(pos[0]) + "," + str(pos[1])+"," + str(pos[2]) + ")")
    return

def orderBuildFleet(id, ships, name):
    '''
    Build a fleet
    id is for the object the order is for
     Arg name: ships    Arg type: List (code:6)    Arg desc: The type of ship to build
     Arg name: name    Arg type: String (code:7)    Arg desc: The name of the new fleet being built
    '''
    global rulesystem
    rulesystem.addConstraint("order_build_fleet(" + str(id) + ", " + str(ships) + "," + name + ")")
    return

def orderColonise(id):
    '''
    Attempt to colonise a planet at the current location
    id is for the object the order is for
    '''
    global rulesystem
    rulesystem.addConstraint("order_colonise(" + str(id) + ")")
    return

def orderSplitFleet(id, ships):
    '''
    Split the fleet into two
    id is for the object the order is for
     Arg name: ships    Arg type: List (code:6)    Arg desc: The ships to be transferred
    '''
    global rulesystem
    rulesystem.addConstraint("order_split_fleet(" + str(id) + ", " + str(ships) + ")")
    return

def orderMergeFleet(id):
    '''
    Merge this fleet into another one
    id is for the object the order is for
    '''
    global rulesystem
    rulesystem.addConstraint("order_merge_fleet(" + str(id) + ")")
    return

def orderNone(id):
    '''
    Removes orders from the object.
    '''
    global rulesystem
    rulesystem.addConstraint("order_none(" + str(id) + ")")
    return

def executeOrdersNone(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_none(int)")
    for orderConstraint in orders:
        executeOrder(cache, connection, objectId, None)

def executeOrdersNoOperation(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_no_operation(int,int)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        wait = int(args[1])
        ordertype = findOrderDesc("No Operation")
        args = [0, objectId, -1, ordertype.subtype, 0, [], wait]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersMove(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_move(int,int,int,int)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        pos = [[int(args[1]), int(args[2]), int(args[3])]]
        ordertype = findOrderDesc("Move")
        args = [0, objectId, -1, ordertype.subtype, 0, [], pos]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersBuildFleet(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_build_fleet(int,list,str)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        ships = [[], args[1]]
        name = [len(args[2]), args[2]]
        ordertype = findOrderDesc("Build Fleet")
        args = [0, objectId, -1, ordertype.subtype, 0, [], ships, name]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersColonise(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_colonise(int)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        ordertype = findOrderDesc("Colonise")
        args = [0, objectId, -1, ordertype.subtype, 0, []]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersSplitFleet(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_split_fleet(int,list)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        ships = [[], args[1]]
        ordertype = findOrderDesc("Split Fleet")
        args = [0, objectId, -1, ordertype.subtype, 0, [], ships]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersMergeFleet(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_merge_fleet(int)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        ordertype = findOrderDesc("Merge Fleet")
        args = [0, objectId, -1, ordertype.subtype, 0, []]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrder(cache, connection, objectId, order):
    # get the queue for the object
    queueid = extra.objectutils.getOrderQueueList(cache, objectId)[0][1]
    queue = cache.orders[queueid]
    node = queue.first
    
    #check if there is no existing order
    if order != None and queue.first.CurrentOrder is None:
        # make a new order   
        evt = cache.apply("orders", "create after", queueid, node, order)
        tp.client.cache.apply(connection, evt, cache)
    #check if the existing order is the same as current order
    elif not checkIfOrdersSame(node.CurrentOrder, order):
        if order != None:
            #replace the current order with the new one
            evt = cache.apply("orders", "change", queueid, node, order)
            tp.client.cache.apply(connection, evt, cache)
        #delete order
        else:
            nodes = [x for x in queue]
            evt = cache.apply("orders", "remove", queueid, nodes=nodes)
            tp.client.cache.apply(connection, evt, cache)

def checkIfOrdersSame(order1, order2):
    #check if both are None
    if order1 is None and order2 is None:
        return True
    
    #check the type
    if type(order1) != type(order2):
        return False
    #check the name TODO: might be included in type
    if order1._name != order2._name:
        return False
    #check the order arguments
    if order1.properties != order2.properties:
        return False
    return True

def findOrderDesc(name):
    name = name.lower()
    for d in OrderDescs().values():
        if d._name.lower() == name:
            return d

def buildScout(planetID):
    orderBuildFleet(planetID, [(helper.designByName("scout"), 1)], "Scout Fleet")
    
def buildFrigate(planetID):
    orderBuildFleet(planetID, [(helper.designByName("frigate"), 1)], "Frigate Fleet")
    
def buildBattleship(planetID):
    orderBuildFleet(planetID, [(helper.designByName("battleship"), 2)], "Battleship Fleet")

def AICode():
    print "Now in python mode!"
    global rulesystem
    
    helper.printAboutMe()
    planets = []
    
    fleetsWithOrders = []
    battleshipFleets = []
    for fleet in helper.myFleets():
        if helper.name(fleet) == "Battleship Fleet":
            battleshipFleets.append(fleet)
    
    for planet in helper.neutralPlanets():
        fleet = helper.nearestMyFleet(helper.position(planet),fleetsWithOrders+battleshipFleets)
        
        if fleet == None:
            break
        
        if helper.position(fleet) != helper.position(planet):
            print "moving", helper.name(fleet)
            orderMove(fleet, helper.position(planet))
        else:
            print "colonising", helper.name(fleet)
            orderColonise(fleet)
        fleetsWithOrders += [fleet]
        
    #attack with all fleets without orders
    for fleet in helper.myFleets():
        if not fleet in fleetsWithOrders:
            planet = helper.nearestEnemyPlanet(fleet)
            if planet:
                orderMove(fleet, helper.position(planet))
      
    #build one frigate or one battleship on every planet
    for myPlanet in helper.myPlanets():
        if not helper.hasOrder(myPlanet):
            if random.random() < 0.5:
                buildFrigate(myPlanet)
            else:
                buildBattleship(myPlanet)
    return
