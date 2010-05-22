'''
@author: Damjan 'Null' Kosir
'''
import logging
import tp.client.cache
from tp.netlib.objects import OrderDescs
import extra.objectutils
import helper

rulesystem = None

constraints = """order_no_operation(int,int)
order_move(int,int,int,int)
order_build_fleet(int,list,str)
order_build_weapon(int,list)
order_colonise(int)
order_split_fleet(int,list)
order_merge_fleet(int)
order_enhance(int,int)
order_send_points(int,list)
order_load_armament(int,list)
order_unload_armament(int,list)
order_none(int)""".split('\n')

def endTurn(cache2, rs, connection2):
    global rulesystem
    global cache
    global connection
    #update globals
    rulesystem = rs
    cache = cache2
    connection = connection2
    helper.rulesystem = rulesystem
    helper.cache = cache
    helper.connection = connection
    
    AICode()
    executeOrdersNoOperation(cache, connection)
    executeOrdersMove(cache, connection)
    executeOrdersBuildFleet(cache, connection)
    executeOrdersBuildWeapon(cache, connection)
    executeOrdersColonise(cache, connection)
    executeOrdersSplitFleet(cache, connection)
    executeOrdersMergeFleet(cache, connection)
    executeOrdersEnhance(cache, connection)
    executeOrdersSendPoints(cache, connection)
    executeOrdersLoadArmament(cache, connection)
    executeOrdersUnloadArmament(cache, connection)

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
    rulesystem.addConstraint("order_move(" + str(id) + ", " + str(pos[0]) + "," + str(pos[1]) + "," + str(pos[2]) + ")")
    return

def orderBuildFleet(id, ships, name):
    '''
    Build a fleet
    id is for the object the order is for
     Arg name: Ships    Arg type: List (code:6)    Arg desc: The type of ship to build
     Arg name: Name    Arg type: String (code:7)    Arg desc: The name of the new fleet being built
    '''
    global rulesystem
    rulesystem.addConstraint("order_build_fleet(" + str(id) + ", " + str(ships) + ", " + name + ")")
    return

def orderBuildWeapon(id, weapons):
    '''
    Build a Weapon
    id is for the object the order is for
     Arg name: Weapons    Arg type: List (code:6)    Arg desc: The type of weapon to build
    '''
    global rulesystem
    rulesystem.addConstraint("order_build_weapon(" + str(id) + ", " + str(weapons) + ")")
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

def orderEnhance(id, points):
    '''
    Enhance your Production
    id is for the object the order is for
     Arg name: Points    Arg type: Time (code:1)    Arg desc: The number of points you want to enhance with.
    '''
    global rulesystem
    rulesystem.addConstraint("order_enhance(" + str(id) + ", " + str(points) + ")")
    return

def orderSendPoints(id, planet):
    '''
    Send Production Points
    id is for the object the order is for
     Arg name: Planet    Arg type: List (code:6)    Arg desc: The Planet to send points to.
    '''
    global rulesystem
    rulesystem.addConstraint("order_send_points(" + str(id) + ", " + str(planet) + ")")
    return

def orderLoadArmament(id, weapons):
    '''
    Load a weapon onto your ships
    id is for the object the order is for
     Arg name: Weapons    Arg type: List (code:6)    Arg desc: The weapon to load
    '''
    global rulesystem
    rulesystem.addConstraint("order_load_armament(" + str(id) + ", " + str(weapons) + ")")
    return

def orderUnloadArmament(id, weapons):
    '''
    Unload a weapon onto your ships
    id is for the object the order is for
     Arg name: Weapons    Arg type: List (code:6)    Arg desc: The weapon to unload
    '''
    global rulesystem
    rulesystem.addConstraint("order_unload_armament(" + str(id) + ", " + str(weapons) + ")")
    return

def orderNone(id):
    '''
    Removes orders from the object.
    '''
    global rulesystem
    rulesystem.addConstraint("order_none(" + str(id) + ")")
    return

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
        args = [0, objectId, -1, ordertype.subtype, 0, [], Ships, Name]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersBuildWeapon(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_build_weapon(int,list)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        weapons = [[], args[1]]
        ordertype = findOrderDesc("Build Weapon")
        args = [0, objectId, -1, ordertype.subtype, 0, [], Weapons]
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

def executeOrdersEnhance(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_enhance(int,int)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        points = int(args[1])
        ordertype = findOrderDesc("Enhance")
        args = [0, objectId, -1, ordertype.subtype, 0, [], Points]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersSendPoints(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_send_points(int,list)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        planet = [[], args[1]]
        ordertype = findOrderDesc("Send Points")
        args = [0, objectId, -1, ordertype.subtype, 0, [], Planet]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersLoadArmament(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_load_armament(int,list)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        weapons = [[], args[1]]
        ordertype = findOrderDesc("Load Armament")
        args = [0, objectId, -1, ordertype.subtype, 0, [], Weapons]
        order = ordertype(*args)
        executeOrder(cache, connection, objectId, order)

def executeOrdersUnloadArmament(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_unload_armament(int,list)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        weapons = [[], args[1]]
        ordertype = findOrderDesc("Unload Armament")
        args = [0, objectId, -1, ordertype.subtype, 0, [], Weapons]
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

def waitingAI():
    print "I am lazy."
    return

def commandoAI():
    print "I am Rambo."
    return
    
def rushAI():
    print "I am Zerg."
    return
    
def randomAI():
    print "I am confused."
    return
    
def bunkerAI():
    print "I am paranoid"
    return

def greedyAI():
    print "I am not wealthy enough"
    return
    
def multipleAI():
    print "I am a shapeshifter."
    return

def AICode():
    helper.addDesign("name","description",helper.findCategoryByName("ships"),[[helper.findComponentByName("scout hull"),1]])
    return
