'''
@author: Damjan 'Null' Kosir
'''
import logging
import tp.client.cache
from tp.netlib.objects import OrderDescs
import extra.objectutils
import helper
import random
from time import sleep
import math

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

def executeOrdersBuildWeapon(cache, connection):
    global rulesystem
    orders = rulesystem.findConstraint("order_build_weapon(int,list)")
    for orderConstraint in orders:
        args = orderConstraint.args
        objectId = int(args[0])
        weapons = [[], args[1]]
        ordertype = findOrderDesc("Build Weapon")
        args = [0, objectId, -1, ordertype.subtype, 0, [], weapons]
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
        args = [0, objectId, -1, ordertype.subtype, 0, [], planet]
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
        args = [0, objectId, -1, ordertype.subtype, 0, [], weapons]
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
        args = [0, objectId, -1, ordertype.subtype, 0, [], weapons]
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
           
def canColonise(fleet):
    listOfShips = helper.shipsOfFleet(fleet)
    for (type, design, number) in listOfShips:
        if helper.designPropertyValue(design, "colonise") == "Yes":
            return True
    return False

def waitingAI():
    print "I am lazy."
    return

def addShipDesign(components):
    helper.addDesign(helper.generateDesignName(components), "", helper.categoryByName("ships"), components)
    
def addWeaponDesign(components):
    helper.addDesign(helper.generateDesignName(components), "", helper.categoryByName("weapons"), components)

#serial number for numbering fleets when naming for tracking purposes
fleetSerialNumber = 0

def buildShip(planet, ship):
    global fleetSerialNumber
    print "building ships on", helper.name(planet)
    orderBuildFleet(planet, [(ship, 1)], helper.playerName(helper.whoami()) + "'s fleet #" + str(fleetSerialNumber))
    fleetSerialNumber += 1
    
def buildWeapon(planet, weapon):
    print "building weapons on" , helper.name(planet)
    orderBuildWeapon(planet, [(weapon, 1)])

def moveToObject(objectToMove, objectToMoveTo):
    orderMove(objectToMove, helper.position(objectToMoveTo))
    
def orderOfID(objectId):
    #TODO think about adding this to helper or at least a has order function
    # get the queue for the object
    queueid = extra.objectutils.getOrderQueueList(cache, objectId)[0][1]
    queue = cache.orders[queueid]
    #return current order
    return queue.first.CurrentOrder

def designWeapon(type, explosive):
    '''
    Creates a design for a weapon of specified type using the maximum amount of specified explosives. Returns the id of the design.
    Example: for delta missile with uranium explosives use designWeapon("delta","uranium explosives")
    '''
    #TODO this could be global
    weaponSize = {"alpha":3.0, "beta":6.0, "gamma":8.0, "delta":12.0, "epsilon":24.0, "omega":40.0, "upsilon":60.0, "tau":80.0, "sigma":110.0, "rho":150.0, "xi":200.0}
    explosiveSize = {"uranium explosives":4.0, "thorium explosives":4.5, "cerium explosives":3.0, "enriched uranium":2.0, "massivium":12.0, "antiparticle explosives":0.8, "antimatter explosives":0.5}
    weaponHullDict = {"alpha":helper.componentByName("alpha missile hull"), "beta":helper.componentByName("beta missile hull"), "gamma":helper.componentByName("gamma missile hull"), "delta":helper.componentByName("delta missile hull"), "epsilon":helper.componentByName("epsilon missile hull"), "omega":helper.componentByName("omega torpedoe hull"), "upsilon":helper.componentByName("upsilon torpedoe hull"), "tau":helper.componentByName("tau torpedoe hull"), "sigma":helper.componentByName("sigma torpedoe hull"), "rho":helper.componentByName("rho torpedoe hull"), "xi":helper.componentByName("xi torpedoe hull")}
    
    #make a list of components to use (and calculate the max amount of explosives)
    components = [(weaponHullDict[type], int(math.floor(weaponSize[type] / explosiveSize[explosive])))]
    addWeaponDesign(components)
    return helper.designByName(helper.generateDesignName(components)) 

def maxWeaponsOfDesign(design):
    '''
    Returns a dictionary of types of weapons the design (name or id) can carry. {"alpha":4,"beta":1,...}
    '''
    global cache
    if isinstance(design, str):
        design = helper.designByName(design)

    #TODO this could be made global
    tubeDict = {helper.componentByName("alpha missile tube"):"alpha", helper.componentByName("beta missile tube"):"beta", helper.componentByName("gamma missile tube"):"gamma", helper.componentByName("delta missile tube"):"delta", helper.componentByName("epsilon missile tube"):"epsilon", helper.componentByName("omega torpedoe tube"):"omega", helper.componentByName("upsilon torpedoe tube"):"upsilon", helper.componentByName("tau torpedoe tube"):"tau", helper.componentByName("sigma torpedoe tube"):"sigma", helper.componentByName("rho torpedoe tube"):"rho", helper.componentByName("xi torpedoe tube"):"xi"}
    missileRackDict = {helper.componentByName("alpha missile rack"):"alpha", helper.componentByName("beta missile rack"):"beta", helper.componentByName("gamma missile rack"):"gamma", helper.componentByName("delta missile rack"):"delta", helper.componentByName("epsilon missile rack"):"epsilon"}
    torpedoRackDict = {helper.componentByName("omega torpedoe rack"):"omega", helper.componentByName("upsilon torpedoe rack"):"upsilon", helper.componentByName("tau torpedoe rack"):"tau", helper.componentByName("sigma torpedoe rack"):"sigma", helper.componentByName("rho torpedoe rack"):"rho", helper.componentByName("xi torpedoe rack"):"xi"}
        
    weapons = {}
    for (component, numberOfUnits) in cache.designs[design].components:
        #is the component a tube?
        #each tube can carry 1 weapon
        if tubeDict.has_key(component):
            type = tubeDict[component]
            if weapons.has_key(type):
                weapons[type] += numberOfUnits 
            else:
                weapons[type] = numberOfUnits
            continue
        #is the component a missile rack?
        #each missile rack can carry 2 weapons
        if tubeDict.has_key(component):
            type = tubeDict[component]
            if weapons.has_key(type):
                weapons[type] += numberOfUnits * 2 
            else:
                weapons[type] = numberOfUnits * 2
            continue
        #is the component a torpedo rack?
        #each torpedo rack can carry 4 weapons
        if tubeDict.has_key(component):
            type = tubeDict[component]
            if weapons.has_key(type):
                weapons[type] += numberOfUnits * 4 
            else:
                weapons[type] = numberOfUnits * 4
            continue
        #this component doesn't affect the number of weapons directly
    return weapons

def maxWeaponsOfFleet(fleetid):
    '''
    Returns a dictionary of types of weapons the fleet can carry. {"alpha":4,"beta":1,...}
    '''
    maxWeapons = {}
    #find out the sum of weapons all the ships in this fleet can hold (and ther types)
    for (something, design, number) in helper.shipsOfFleet(fleetid):
        tempMaxWeapons = maxWeaponsOfDesign(design)
        #add all the weapons to the sum
        for weaponType in tempMaxWeapons.keys():
            if maxWeapons.has_key(weaponType):
                maxWeapons[weaponType] += tempMaxWeapons[weaponType] * number
            else:
                maxWeapons[weaponType] = tempMaxWeapons[weaponType] * number
    return maxWeapons

def typeOfWeapon(design):
    '''
    Returns the type of weapon. Example if the design contains an alpha missile hull the function returns "alpha"
    '''
    #TODO make this global and initialse it only once
    reverseWeaponHullDict = {helper.componentByName("alpha missile hull"):"alpha", helper.componentByName("beta missile hull"):"beta", helper.componentByName("gamma missile hull"):"gamma", helper.componentByName("delta missile hull"):"delta", helper.componentByName("epsilon missile hull"):"epsilon", helper.componentByName("omega torpedoe hull"):"omega", helper.componentByName("upsilon torpedoe hull"):"upsilon", helper.componentByName("tau torpedoe hull"):"tau", helper.componentByName("sigma torpedoe hull"):"sigma", helper.componentByName("rho torpedoe hull"):"rho", helper.componentByName("xi torpedoe hull"):"xi"}
    components = helper.designComponents()
    #loop through all components and look for a match
    for (id, value) in component:
        if reverseWeaponHullDict.has_key(id):
            return reverseWeaponHullDict[id]
    return None

def weaponsNeeded(fleetid):
    '''
    Returns a dictionary of weapons that can be loaded by type {"alpha":3,"delta":1,...}
    '''
    maxWeapons = maxWeaponsOfFleet(fleetid)
    #get the weapons already loaded on board the fleet [(resource id, number of units),...]
    weaponsLoaded = weaponsOnObject(fleetid)
    # a dictionary for weapons that could be loaded by type
    weaponsNeededDict = {}
    for type in maxWeapons.keys():
        if weaponsLoaded.has_key(type):
            if maxWeapons[type] > weaponsLoaded[type]:
                weaponsNeededDict[type] = maxWeapons[type] - weaponsLoaded[type]
        else:
            weaponsNeededDict[type] = maxWeapons[type]
    return weaponsNeededDict

def weaponsOnObject(objectid):
    '''
    Returns a dictionary of weapons on this object (available on planet or loaded on fleet) by type. {"alpha":3,"delta":1,...}
    '''
    stuffOnObject = [(resource[0], resource[1]) for resource in helper.resources(objectid)]
    #build a dict of all the weapons loaded by type
    weaponsLoaded = {}
    for (id, number) in stuffOnObject:
        #find a design id from the resource id (they have the same name)
        resourceName = helper.resourceName(id)
        designid = helper.designByName(resourceName)
        if designid == None:
            #resource is not a weapon
            continue
        type = typeOfWeapon(designid)
        if type == None:
            #design not a weapon design
            continue
        #add to the list of weapons
        if weaponsLoaded.has_key(type):
            weaponsLoaded[type] += number
        else:
            weaponsLoaded[type] = number
    return weaponsLoaded
            
def loadWeapons(fleet, planet, weaponDict, alreadyLoaded={}):
    '''
    Gives a Load Armament order for all weapons in the weapon dictionary.
    Already loaded dictionary provides how many weapons of each type have already been asigned to other ships.
    '''
    stuffOnPlanet = [(resource[0], resource[1]) for resource in helper.resources(planet)]
    stuffToLoad = []
    
    #make a copy so we don't change the original
    alreadyLoaded = alreadyLoaded.copy()
    weaponDict = weaponDict.copy()

    #for every type we need to load
    for typeToLoad in weaponDict.keys():
        #loop through all the resources on the planet until we add enough weapons of this type to the loading list
        for (id, available) in stuffOnPlanet:
            #find a design id from the resource id (they have the same name)
            resourceName = helper.resourceName(id)
            designid = helper.designByName(resourceName)
            if designid == None:
                #resource is not a weapon
                continue
            type = typeOfWeapon(designid)
            if type == None:
                #design not a weapon design
                continue
            #check the type of the weapon
            if type == typeToLoad:
                #how many are to be loaded to other ships
                markedForLoading = 0
                if alreadyLoaded.has_key(type):
                    markedForLoading = alreadyLoaded[type]
                #number of weapon we can load
                canLoad = available - markedForLoading
                #if we can load any of them
                if canLoad > 0:
                    willLoad = min(canLoad, weaponDict[type])
                    #add weapons to the list of weapons to load
                    stuffToLoad.append((id, willLoad))
                    
                    #reduce the number of this type that need loading
                    weaponDict[type] -= willLoad
                    
                    #we have passed all the weapons that were marked for other ships
                    alreadyLoaded[type] = 0
                    
                    #continue to another type if all weapons of this type have been marked for loading
                    if weaponDict[type] == 0:
                        break
                #all are to be loaded to ther ships    
                else:
                    alreadyLoaded[type] -= available
                
            #add to the list of weapons
            if weaponsLoaded.has_key(type):
                weaponsLoaded[type] += number
            else:
                weaponsLoaded[type] = number
    
    assert stuffToLoad != []
    orderLoadArmament(fleet, stuffToLoad)

def commandoAI():

    print "I am Rambo."
    #this code will be very similar to rushAI (only with stronger ships)
    return

invasionFleets = []

def rushAI():
    '''
    AI player that builds large armies of cheap units and attacks in waves.
    '''
    global invasionFleets
    print "I am Zerg."
    
    #number of ships and weapons needed to start an invasion
    invasionShips = 10
    #retreat if less than this number of ships marked for invasion
    invasionShipsRetreat = 3
    
    #construct a design for a simple attack/colonisation ship
    ship = []
    ship.append([helper.componentByName("frigate"), 1])
    ship.append([helper.componentByName("colonisation module"), 1]) #TODO uncomment this when the design bug is fixed
    ship.append([helper.componentByName("delta missile tube"), 1])
    ship.append([helper.componentByName("delta missile rack"), 1])
    #add the design
    addShipDesign(ship)
    shipName = helper.generateDesignName(ship)
    #replace the list of components with the id
    ship = helper.designByName(shipName)
    
    #choose a cheap explosives for use in weapons
    explosives = "uranium explosives"
    
    #build ships on all planets (and load them with weapons)
    for myPlanet in helper.myPlanets():
        currentOrder = orderOfID(myPlanet) 
        print "checking what to do with", helper.name(myPlanet)
        #check if there is already something being build on this planet
        if currentOrder == None:
            #load ships with weapons and build more weapons if necessary
            #what type of weapon should be build
            weaponToBuild = None

            weaponsOnPlanet = weaponsOnObject(myPlanet)
            #weapons already loaded
            weaponsLoadedDict = {}
            
            for thingOnPlanet in helper.contains(myPlanet):
                if helper.isMyFleet(thingOnPlanet):
                    #find out if it needs any more weapons
                    weaponsNeededDict = weaponsNeeded(thingOnPlanet)
                    #if no needed weapons skip this fleet
                    if len(weaponsNeededDict) == 0:
                        continue
                    
                    #make a list of all weapons that will be loaded
                    weaponsToLoadDict = {}
                    for typeOfWeaponNeeded in weaponsNeededDict.keys():
                        available = 0
                        if weaponsOnPlanet.has_key(typeOfWeaponNeeded):
                            available = weaponsOnPlanet[typeOfWeaponNeeded]
                            if weaponsLoadedDict.has_key(typeOfWeaponNeeded):
                                available -= weaponsLoadedDict[typeOfWeaponNeeded]
                            assert available >= 0
                            #give build order if nesessary
                            if weaponToBuild == None and available < weaponsNeededDict[typeOfWeaponNeeded]:
                                weaponToBuild = typeOfWeaponNeeded
                            #mark weapons for loading
                            weaponsToLoadDict[typeOfWeaponNeeded] = min(available, weaponsNeededDict[typeOfWeaponNeeded])
                    #if there is anything to load
                    if weaponsToLoadDict != {}:
                        #actualy load the weapons...
                        loadWeapons(thingOnPlanet, myPlanet, weaponsToLoadDict, weaponsLoadedDict)
                        #mark them as loaded
                        for type in weaponsToLoadDict.keys():
                            #make sure other ships don't try to load the same weapons
                            if weaponsLoadedDict.has_key(type):
                                weaponsLoadedDict[type] += weaponsToLoadDict[type]
                            else:
                                weaponsLoadedDict[type] = weaponsToLoadDict[type]
                    
            #build weapons/ships order
            if weaponToBuild == None:
                #no weaopns to build... build a ship
                buildShip(myPlanet, ship)
            else:
                #build a weapon of the required type
                buildWeapon(myPlanet, designWeapon(weaponToBuild, explosive))    

    #check how many fleets are available for the invasion
    potentialInvasionFleets = helper.myFleets()
    #remove all of the fleets that are already marked for the invasion and fleets that can no longer fight (no weapons)
    for fleet in invasionFleets:
        potentialInvasionFleets.remove(fleet)
        #if it can no longer attack
        if weaponsOnObject(fleet) == {}:
            print helper.name(fleet), "is no longer invading"
            invasionFleets.remove(fleet)
    #remove all of the fleets that are not fully loaded with weapons
    for fleet in potentialInvasionFleets:
        #remove ship if it's not loaded with weapons
        if weaponsOnObject(fleet) != maxWeaponsOfFleet(fleet):
            potentialInvasionFleets.remove(fleet)
            continue
        
    guardOnPlanets = {}
    allMyPlanets = helper.myPlanets()
    defenceShips = 1
    #mark fleets for invasion
    print "there are", len(potentialInvasionFleets), "fleets ready for invasion"
    if len(potentialInvasionFleets) >= invasionShips:
        for fleet in potentialInvasionFleets:
            parent = helper.containedBy(fleet)        
            #if the fleet is on one of our planets and the number of fleets on that planet
            #is less than the minimum don't send the ships away
            if parent in allMyPlanets:
                #how many fleets are guarding this planet
                currentGuard = 0
                if parent in guardOnPlanets:
                    currentGuard = guardOnPlanets[parent]
                #if not enough fleets are guarding add this one
                if currentGuard < defenceShips:
                    guardOnPlanets[parent] = currentGuard + 1
                    continue
            #mark it for invasion
            invasionFleets.append(fleet)
    
    #make the invasion fleets go back if there are only a few of them left
    if len(invasionFleets) < invasionShipsRetreat:
        print "to little attack ships. Retreat!"
        invasionFleets = [] 
    
    
    allMyFleets = helper.myFleets()
    #attack the enemy with ships marked for invasion
    for fleet in invasionFleets:
        if not fleet in allMyFleets:
            #this is not my fleet anymore... remove it
            invasionFleets.remove(fleet)
        print helper.name(fleet), "is invading (beware!)"
        #find a planet to attack
        nearestPlanet = helper.nearestEnemyPlanet(helper.position(fleet))
        #move to that planet
        if nearestPlanet != None:
            print helper.name(fleet), "is attacking", helper.name(nearestPlanet) 
            planetPosition = helper.position(nearestPlanet)
            if helper.position(fleet) != planetPosition:
                #TODO: I think you can't attack a planet if you're moving there (even if you are there)
                orderMove(fleet, planetPosition)
                #TODO find out if you have to colonise a planet to take it over (I think so)
        else:
            print helper.name(fleet), "has nothing to attack"
    
    #make a list of fleets not marked for invasion
    freeFleets = helper.myFleets()
    for fleet in invasionFleets:
        freeFleets.remove(fleet)
    
    #give orders to ships not marked for invasion
    #move ships to neutral planets and colonise them (leave some ships on every planet for defense)
    defenceShips = 3
    planetsToIgnore = []
    guardOnPlanets = {}
    for fleet in freeFleets:  
        parent = helper.containedBy(fleet)        
        #if the fleet is on one of our planets and the number of fleets on that planet
        #is less than the minimum don't send the ships away
        if parent in allMyPlanets:
            #how many fleets are guarding this planet
            currentGuard = 0
            if parent in guardOnPlanets:
                currentGuard = guardOnPlanets[parent]
            #if not enough fleets are guarding add this one
            if currentGuard < defenceShips:
                guardOnPlanets[parent] = currentGuard + 1
                #make it stay there
                orderNone(fleet)
                continue

        #move only ships that can colonise other planets
        if canColonise(fleet):                
            nearestPlanet = helper.nearestNeutralPlanet(helper.position(fleet), planetsToIgnore)
            planetPosition = helper.position(nearestPlanet)
            planetsToIgnore.append(nearestPlanet)
            
            if helper.position(fleet) == planetPosition:
                #colonise if there
                print helper.name(fleet), "is colonising", helper.name(nearestPlanet)
                orderColonise(fleet)
                pass
            else:
                #move to planet
                print "moving", helper.name(fleet), "to", helper.name(nearestPlanet)
                orderMove(fleet, planetPosition)
        #other ships should go to a friendly palanet for suplies (if not already there)
        else:
            nearestPlanet = helper.nearestMyPlanet(helper.position(fleet))
            planetPosition = helper.position(nearestPlanet)
            #move if not already there
            if helper.position(fleet) != planetPosition:
                print "moving", helper.name(fleet), "to", helper.name(nearestPlanet)
                orderMove(fleet, planetPosition)
    return
    
def randomAI():
    '''
    AI player that selects randomly from a set of predefined actions.
    '''
    print "I am confused."
    #construct a design for a simple attack/colonisation ship
    ship = []
    ship.append([helper.componentByName("frigate"), 1])
    ship.append([helper.componentByName("colonisation module"), 1]) 
    ship.append([helper.componentByName("delta missile tube"), 1])
    ship.append([helper.componentByName("delta missile rack"), 1])
    #add the design
    addShipDesign(ship)
    shipName = helper.generateDesignName(ship)
    #replace the list of components with the id
    ship = helper.designByName(shipName)
    
    #construct a design for a missile that fits the ship
    weapon = []
    weapon.append([helper.componentByName("delta missile hull"), 1])
    weapon.append([helper.componentByName("uranium explosives"), 2])
    #add the design
    addWeaponDesign(weapon)
    weaponName = helper.generateDesignName(weapon)
    #replace the list of components with the id
    weapon = helper.designByName(weaponName)
    
    #give orders to planets
    for myPlanet in helper.myPlanets():
        #only give orders if the planet has none
        if orderOfID(myPlanet) != None:
            print helper.name(myPlanet), "already has orders"
            continue
        #list available actions
        actionList = ["wait", "buildShip", "buildWeapon"]
        
        #pick an action
        action = random.choice(actionList)
        if action == "buildShip":
            buildShip(myPlanet, ship)
            continue
        if action == "buildWeapon":
            buildWeapon(myPlanet, weapon)
            continue
        print "doing nothing on", helper.name(myPlanet)
        
    #give orders to fleets
    for fleet in helper.myFleets():
        #only give orders if the fleet has none
        if orderOfID(fleet) != None:
            print helper.name(fleet), "already has orders"
            continue
        #automatic weapon loading if on friendly planet with weapons
        #TODO this only works for fleets specified earlier
        maxMissiles = 3
        if helper.shipsOfFleet(fleet) == [(9, ship, 1)]: 
            nearestMyPlanet = helper.nearestMyPlanet(fleet)
            if helper.position(fleet) == helper.position(nearestMyPlanet):
                weaponsOnFleet = helper.resourceAvailable(fleet, helper.designName(weapon))
                if weaponsOnFleet < maxMissiles:
                    weaponsOnPlanet = helper.resourceAvailable(nearestMyPlanet, helper.designName(weapon))
                    if weaponsOnPlanet > 0:
                        weaponsToLoad = min(maxMissiles - weaponsOnFleet, weaponsOnPlanet)
                        orderLoadArmament(fleet, [(helper.resourceByName(helper.designName(weapon)), weaponsToLoad)])
        
        #TODO maybe add an automatic colonisation if on neutral planet and can colonise
        
        #list available actions
        actionList = ["wait", "colonise", "attack", "move to friendly planet", "move to neutral planet"]
        #remove colonise option if the fleet can't colonise planets
        if not canColonise(fleet):
            actionList.remove("colonise")
        #remove the colonise option if the fleet is not on an neutral planet
        elif helper.position(fleet) != helper.position(helper.nearestNeutralPlanet(fleet)):            
            actionList.remove("colonise")
        #remove attack option if the fleet has no weapons on board 
        if not helper.resourceAvailable(fleet, helper.designName(weapon)) > 0:
             actionList.remove("attack")
        
        #pick an action
        action = random.choice(actionList)
        if action == "colonise":
            print helper.name(fleet), "is colonising", helper.name(helper.targetPosition(fleet))
            orderColonise(fleet)
            continue
        if action == "attack":
            #find 3 nearest enemy planets
            nearestEnemyPlanets = [helper.nearestEnemyPlanet(fleet)]
            nearestEnemyPlanets.append(helper.nearestEnemyPlanet(fleet, nearestEnemyPlanets))
            nearestEnemyPlanets.append(helper.nearestEnemyPlanet(fleet, nearestEnemyPlanets))
            #remove Nones
            while None in nearestEnemyPlanets:
                nearestEnemyPlanets.remove(None)
            #pick one to attack
            planetToAttack = random.choice(nearestEnemyPlanets) 
            #attack it
            moveToObject(fleet, planetToAttack)
            print helper.name(fleet), "is attacking", helper.name(planetToAttack)
            continue
        if action == "move to friendly planet":
            #find 3 nearest enemy planets
            nearestMyPlanets = [helper.nearestMyPlanet(fleet)]
            nearestMyPlanets.append(helper.nearestMyPlanet(fleet, nearestMyPlanets))
            nearestMyPlanets.append(helper.nearestMyPlanet(fleet, nearestMyPlanets))
            #remove Nones
            while None in nearestMyPlanets:
                nearestMyPlanets.remove(None)
            #pick one to attack
            planetToMoveTo = random.choice(nearestMyPlanets)
                        
            #attack it
            moveToObject(fleet, planetToMoveTo)
            print helper.name(fleet), "is moving to a friendly planet", helper.name(planetToMoveTo)
            continue
        if action == "move to neutral planet":
            #find 3 nearest enemy planets
            nearestNeutralPlanets = [helper.nearestNeutralPlanet(fleet)]
            nearestNeutralPlanets.append(helper.nearestNeutralPlanet(fleet, nearestNeutralPlanets))
            nearestNeutralPlanets.append(helper.nearestNeutralPlanet(fleet, nearestNeutralPlanets))
            #remove Nones
            while None in nearestNeutralPlanets:
                nearestNeutralPlanets.remove(None)
            #pick one to attack
            planetToMoveTo = random.choice(nearestNeutralPlanets) 
            #attack it
            moveToObject(fleet, planetToMoveTo)
            print helper.name(fleet), "is moving to a neutral planet", helper.name(planetToMoveTo)
            continue
        print helper.name(fleet), "is doing nothing"    
    return
    
def bunkerAI():
    print "I am paranoid"
    #this code will be very similar to rushAI (only with different designs=
    return

def greedyAI():
    print "I am not wealthy enough"
    #this code will be very similar to rushAI (only without attacking)
    return
    
def multipleAI():
    print "I am a shapeshifter."
    #randomly choose one of the other behaviours
    import random
    random.choice([rushAI,commandoAI,bunkerAI,greedyAI])()
    return

def AICode():
    if helper.myFleets() == [] and helper.myPlanets() == []:
        print "Today was a good day to die."
        exit(0)
    
    #delete all messages so you don't get spammed
    helper.deleteAllMessages()
    print "It's turn", helper.turnNumber()
    helper.printAboutMe()
    #helper.printDesignsWithProperties()
    if helper.playerName(helper.whoami()) == "ai":
        rushAI()
    else:
        randomAI()
    return

"""\
list of possible components

scout hull
battle scout hull
advanced battle scout hull
frigate
battle frigate
destroyer
battle destroyer
battleship
dreadnought
argonaut

uranium explosives
thorium explosives
cerium explosives
enriched uranium
massivium
antiparticle explosives
antimatter explosives

alpha missile tube
alpha missile rack
alpha missile hull
beta missile tube
beta missile rack
beta missile hull
gamma missile tube
gamma missile rack
gamma missile hull
delta missile tube
delta missile rack
delta missile hull
epsilon missile tube
epsilon missile rack
epsilon missile hull

omega torpedoe tube
omega torpedoe rack
omega torpedoe hull
upsilon torpedoe tube
upsilon torpedoe rack
upsilon torpedoe hull
tau torpedoe tube
tau torpedoe rack
tau torpedoe hull
sigma torpedoe tube
sigma torpedoe rack
sigma torpedoe hull
rho torpedoe tube
rho torpedoe rack
rho torpedoe hull
xi torpedoe tube
xi torpedoe rack
xi torpedoe hull

armor
colonisation module
"""
