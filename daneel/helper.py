'''
Created on 30.4.2010

@author: Damjan 'Null' Kosir
'''
from tp.netlib.objects import Design
import tp.client.cache
import math
import extra

rulesystem = None
cache = None
conection = None

def nearestMyFleet(position, ignore=[]):
    '''
    Finds the nearest fleet owned by you (position or object id). List of fleets to ignore is optional.
    '''
    return nearestFleetOwnedBy(position, whoami(), ignore)

def distance(object1, object2):
    '''
    Returns the distance between given objects
    '''
    return math.sqrt(distanceSqare(object1, object2))

def distanceSqare(object1, object2):
    '''
    Returns the sqare distance between given objects.
    '''
    (x1, y1, z1) = position(object1)
    (x2, y2, z2) = position(object2)
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2

def nearestFleetOwnedBy(targetPosition, owners, ignore=[]):
    '''
    Finds the fleet owned by one of the players in the owners list (can also be an int) nearest to the position (position or object id). List of fleets to ignore is optional.
    '''
    if type(targetPosition) == int:
        targetPosition = position(targetPosition)
    
    if type(owners) == int:
        owners = [owners] 
    (x, y, z) = targetPosition
    fleets = fleetsOwnedBy(owners)
    nearestFleet = None
    minDistance = 1e300
    for fleet in fleets:
        if not fleet in ignore:
            (x2, y2, z2) = position(fleet)
            tempDistance = (x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2 #no need for sqrt
            #find nearest
            if tempDistance < minDistance:
                minDistance = tempDistance
                nearestFleet = fleet
    return nearestFleet

def nearestEnemyPlanet(position, ignore=[]):
    '''
    Finds a planet owned by one of the enemies nearest to the position (position or object id). List of planets to ignore is optional.
    '''
    return nearestPlanetOwnedBy(position, enemies(), ignore)

def nearestMyPlanet(position, ignore=[]):
    '''
    Finds my planet nearest to the position (position or object id). List of planets to ignore is optional.
    '''
    return nearestPlanetOwnedBy(position, whoami(), ignore)

def nearestPlanetOwnedBy(targetPosition, owners, ignore=[]):
    '''
    Finds the planet owned by one of the players in the owners list (can be an int) nearest to the position (position or objectid). List of planets to ignore is optional.
    '''
    if type(targetPosition) == int:
        targetPosition = position(targetPosition)
    
    if type(owners) == int:
        owners = [owners] 
    (x, y, z) = targetPosition
    planets = planetsOwnedBy(owners)
    nearestPlanet = None
    minDistance = 1e300
    for planet in planets:
        if not planet in ignore:
            (x2, y2, z2) = position(planet)
            tempDistance = (x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2 #no need for sqrt
            #find nearest
            if tempDistance < minDistance:
                minDistance = tempDistance
                nearestPlanet = planet
    return nearestPlanet

def nearestNeutralPlanet(targetPosition, ignore=[]):
    '''
    Finds the neutral(not owned by anyone) planet nearest to the position (position or objectid). List of planets to ignore is optional.
    '''
    if type(targetPosition) == int:
        targetPosition = position(targetPosition)
    
    (x, y, z) = targetPosition
    planets = neutralPlanets()
    nearestPlanet = None
    minDistance = 1e300
    for planet in planets:
        if not planet in ignore:
            (x2, y2, z2) = position(planet)
            tempDistance = (x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2 #no need for sqrt
            #find nearest
            if tempDistance < minDistance:
                minDistance = tempDistance
                nearestPlanet = planet
    return nearestPlanet

def myFleets():
    '''
    Returns a list of all fleets owned by you.
    '''
    global rulesystem
    fleets = rulesystem.findConstraint("fleet(int)")
    list = []
    for x in fleets:
        if owner(x.args[0]) == whoami():
            list += [int(x.args[0])]
    return list

def fleets():
    '''
    Returns a list of all fleets.
    '''
    global rulesystem
    fleets = rulesystem.findConstraint("fleet(int)")
    list = []
    for x in fleets:
        list += [int(x.args[0])]
    return list

def enemyFleets():
    '''
    Returns a list of enemy fleets.
    '''
    return fleetsOwnedBy(enemies())

def fleetsOwnedBy(owners):
    '''
    Returns a list of all fleets owned by any player in the owners list (can be an int).
    '''
    global rulesystem
    if type(owners) == int:
        owners = [owners]
    
    fleets = rulesystem.findConstraint("fleet(int)")
    list = []
    for x in fleets:
        if owner(x.args[0]) in owners:
            list += [int(x.args[0])]
    return list

def stars():
    '''
    Returns a list of all the stars.
    '''
    global rulesystem
    stars = rulesystem.findConstraint("star(int)")
    return [int(x.args[0]) for x in stars]

def containedBy(id):
    '''
    Return the object id that contains (is parent of) the object with the given id
    '''
    global cache
    return cache.objects[id].parent 

def contains(id):
    '''
    Returns a list of all the object the object with the given object contains.
    '''
    global rulesystem
    things = rulesystem.findConstraint("contains(int,int)")
    list = []
    for x in things:
        if int(x.args[0]) == id:
            list += [x.args[1]] 
    return list

def position(id):
    '''
    Returns the position of the object with the given id.
    '''
    global rulesystem
    pos = rulesystem.findConstraint("pos(int,int,int,int)")
    for x in pos:
        if int(x.args[0]) == id:
            return [x.args[1], x.args[2], x.args[3]] 
    return None

def velocity(id):
    '''
    Returns the velocity of the object with the given id.
    '''
    global rulesystem
    pos = rulesystem.findConstraint("vel(int,int,int,int)")
    for x in pos:
        if int(x.args[0]) == id:
            return [x.args[1], x.args[2], x.args[3]] 
    return None

def name(id):
    '''
    Returns the name of the object with the given id. (not to be used for player names)
    '''
    global rulesystem
    name = rulesystem.findConstraint("name(int,str)")
    for x in name:
        if int(x.args[0]) == id:
            return x.args[1] 
    return None

def owner(id):
    '''
    Returns the owner (player) of the object with the given id.
    '''
    global rulesystem
    things = rulesystem.findConstraint("owner(int,int)")
    for x in things:
        if int(x.args[0]) == id:
            return x.args[1] 
    return None

def whoami():
    '''
    Returns your player id.
    '''
    global rulesystem
    return rulesystem.findConstraint("whoami(int)")[0].args[0]

def turnNumber():
    '''
    Returns the number of the current turn.
    '''
    global rulesystem
    return rulesystem.findConstraint("turn(int)")[0].args[0]

def playerByName(playerName):
    for player in players():
        if name(player) == playerName:
            return player
    return None

def players():
    '''
    Returns a list of all the players. (including guest)
    '''
    global rulesystem
    return [player.args[0] for player in rulesystem.findConstraint("player(int,unicode)")[1:]]

def playersWithoutGuest():
    '''
    Returns a list of all the real players. (without guest)
    '''
    allPlayers = players()
    #remove guest (a player who is always present and has no objects)
    print "I am", whoami(), ". My name is", playerName(whoami())
    for player in allPlayers:
        print player, " ", playerName(player)
        if name(player) == "guest":
            allPlayers.remove(player)
            break
    return allPlayers

def playerName(id):
    '''
    Returns the name of the player with the given id.
    '''
    global rulesystem
    players = rulesystem.findConstraint("player(int,unicode)")
    for player in players:
        if player.args[0] == id:
            return player.args[1]
    return None

def myName():
    '''
    Returns your player name.
    '''
    return playerName(whoami())

def enemies():
    '''
    Returns a list of all the enemy playes.
    '''
    players = playersWithoutGuest()
    if whoami() in players:
        players.remove(whoami())
    return players

def printAboutMe():
    '''
    Prints information about you. (name, enemies, fleets and planets owned)
    '''
    print "I am", whoami(), ". My name is", playerName(whoami())
    for x in enemies():
        print x , "(" + playerName(x) + ") is my enemy"
    for x in myFleets():
        print x , "(" + name(x) + ") is my fleet"
    for x in planetsOwnedBy([whoami()]):
        print x, "(" + name(x) + ") is my planet"
    for x in planetsOwnedBy(enemies()):
        print x, "(" + name(x) + ") is my enemies planet"

def printDesigns():
    '''
    Prints all of the available designs. (id, name)
    '''
    global cache
    for design in cache.designs.values():
        print design.id, design.name
        
def printDesignsWithProperties():
    '''
    Prints all of the available designs. (id, name)
    '''
    global cache
    for design in cache.designs.values():
        print design.id, design.name
        for (id, value) in design.properties:
            print id, propertyName(id), ":", value
        print
                 

def printDesign(design):
    '''
    Prints information about the design (name or id). (name, list of components)
    '''
    global cache
    if type(design) != int:
        design = designByName(design)
    print cache.designs[design].name
    for (id, value) in cache.designs[design].properties:
        print cache.properties[id].name, ":", value

def planets():
    '''
    Returns a list of all planets.
    '''
    global rulesystem
    return [planet.args[0] for planet in rulesystem.findConstraint("planet(int)")]

def myPlanets():
    '''
    Returns a list of all planest owned by you.
    '''
    return planetsOwnedBy(whoami())

def planetsOwnedBy(owners):
    '''
    Returns a list of all planets owned by any of the players in the owners list (can be an int).
    '''
    if isinstance(owners, int):
        owners = [owners]
    allPlanets = planets()
    planetList = []
    for planet in allPlanets:
        if owner(planet) in owners:
            planetList += [planet]
    return planetList

def enemyPlanets():
    '''
    Returns a list of enemy planets.
    '''
    return planetsOwnedBy(enemies())
    
def neutralPlanets():
    '''
    Returns a list of all neutral planets.
    '''
    allPlanets = planets()
    planetList = []
    for planet in allPlanets:
        if not owner(planet) in players():
            planetList += [planet]
    return planetList

def addDesign(name, description, categories, componentList, replaceOnDuplicate=False):
    '''
    Adds a new design.
    Categories can be a list or an int.
    Component list must be in format [(partId,numberOfParts),(...),...]
    Replace on duplicate must be set to true if you want to overwrite the existing design with the same name. 
    '''
    current = designByName(name)
    if current != None and not replaceOnDuplicate:
        #design already exists and we don't want to replace it
        return
    global cache
    global connection
    if type(categories) == int:
        categories = [categories]
    #prepare design
    design = Design(-1, -1, 0, categories, name, description, 0, whoami(), componentList, "", [])
    if current == None:
        #create a new design
        print "adding design", name
        evt = cache.CacheDirtyEvent("designs", "create", -1, design)
    else:
        #replace the existing design
        print "replacing design", name
        evt = cache.CacheDirtyEvent("designs", "create", current, design)
        
    #apply changes
    tp.client.cache.apply(connection, evt, cache)
    
    #update the cache by force or the new design won't be available
    #TODO there must be a more elegant way to do this (this way is a bit scary)
        
    if current == None:
        #find the new design id
        oldDesignIDs = [tempDesign.id for tempDesign in cache.designs.values()]
        oldDesignIDs.remove(-1)
        allDesignIDs = [x[0] for x in connection.get_design_ids(iter=True)]
        for x in oldDesignIDs:
            allDesignIDs.remove(x)
        #there should be only one left
        assert len(allDesignIDs) == 1
        
        newDesign = connection.get_designs(allDesignIDs[0])[0]
            
        #find the design to be replaced
        for designNumber in cache.designs:
            if cache.designs[designNumber].id == -1:
                #replace the design
                cache.designs[designNumber] = newDesign
                break
     
    
def nop(group=None, state=None, message=None, todownload=None, amount=None):
    '''
    It does nothing and is used internaly.
    '''
    return

def hasOrder(objectId):
    '''
    Returns True if the object already has an order.
    '''
    # get the queue for the object
    queueid = extra.objectutils.getOrderQueueList(cache, objectId)[0][1]
    queue = cache.orders[queueid]
    #return if there is no order
    return queue.first.CurrentOrder != None

def categoryByName(name):
    '''
    Returns the id of the category with a given name.
    '''
    global cache
    #loop through all categories
    for category in cache.categories.values():
        if category.name.lower() == name.lower():
            #return on match
            return category.id
    return None

def componentByName(name):
    '''
    Returns the id of the component with the given name.
    '''
    global cache
    #loop through all components
    for component in cache.components.values():
        if component.name.lower() == name.lower():
            #return on match
            return component.id
    return None

def componentName(id):
    '''
    Returns the name of the component with the given id.
    '''
    global cache
    return cache.components[id].name

def resourceByName(name):
    '''
    Returns the id of the resource with the given name.
    '''
    global cache
    for resource in cache.resources.values():
        if resource.name.lower() == name.lower():
            return resource.id
    return None

def resourceName(id):
    '''
    Returns the name of the reousrce with the given id.
    '''
    global cache
    for resource in cache.resources.values():
        if resource.id == id:
            return resource.name
    return None

def resourceAvailable(id, resource):
    '''
    Returns the number of units of the resource that are available at the object with the given id.
    Resource can be the name or the id of the resource.
    '''
    global cache
    if type(resource) != int:
        resource = resourceByName(resource)
    
    for tempResource in cache.objects[id].Resources[0][0]:
        if tempResource[0] == resource:
            return tempResource[1]
    return 0

def resources(id):
    '''
    Returns a list of all resources of the object with the given id. [(resourceID,stored,minable,inacc),...]
    '''
    global cache
    return cache.objects[id].Resources[0][0]

def printResources():
    '''
    Prints all resources (id, name).
    '''
    global cache
    for resource in cache.resources.values():
        print resource.id, resource.name

def printResourcesOfId(id):
    '''
    Prints all resources of the object with the given id (stored, minamble, inacc., name, id).
    '''
    global cache
    print "Resources of", name(id), "(id:", id, ")"
    for tempResource in cache.objects[id].Resources[0][0]:
        (resourceID, stored, minable, inacc) = tempResource
        resourceName = ""    
        for resource in cache.resources.values():
            if resource.id == resourceID:
                resourceName = resource.name
                break;
        print stored, minable, inacc, resourceName, "(id:", resourceID, ")"

def designByName(name):
    '''
    Returns the id of the design with the given name.
    '''
    global cache
    #loop through all designs
    for design in cache.designs.values():
        if design.name.lower() == name.lower() and design.owner == whoami():
            #return on match
            return design.id
    return None

def designName(id):
    '''
    Returns the name of the design with the given id.
    '''
    global cache
    #loop through all designs
    for design in cache.designs.values():
        if design.id == id and design.owner == whoami():
            #return on match
            return design.name
    return None

def designComponents(id):
    '''
    Returns a list of components used in the design with the given id. [(part ID,number of parts),(...,...),...]
    '''
    global cache
    return cache.designs[id].components
    
def generateDesignName(components):
    '''
    Generate an unique name based on components.
    '''
    #sort the components by id
    components.sort()
    name = ""
    for component in components:
        #find the component with the given id
        for tempComponent in cache.components.values():
            if tempComponent.id == component[0]:
                #add component information to name
                name += str(component[1]) + "x " + tempComponent.name + " "
                break
    return name.strip()
    
def propertyByName(name):
    '''
    Returns the id of the property with the given name. 
    '''
    global cache
    for property in cache.properties.values():
        if property.name.lower() == name.lower():
            return property.id
    return None

def propertyByDescription(desc):
    '''
    Returns the id of the property with the given description. 
    '''
    global cache
    for property in cache.properties.values():
        if property.description.lower() == desc.lower():
            return property.id
    return None

def propertyName(property):
    '''
    Returns the name of the property with the given id.
    '''
    global cache
    return cache.properties[property].name
   
def designProperties(design):
    '''
    Returns a list of properties of the given design (name or id). [(propertyID,propertyValue),(...,...),...]
    '''
    global cache
    if type(design) != int:
        design = designByName(design)
    return cache.designs[design].properties    

def designPropertyValueByDescription(design, propertyDescription):
    '''
    Returns the value of the property (with given description) in the design (name or id).
    '''
    return designPropertyValue(design, propertyByDescription(propertyDescription))

def designPropertyValue(design, property):
    '''
    Returns the value of the property (id or name) in the design (name or id).
    '''
    global cache
    if type(property) != int:
        property = propertyByName(property)
    properties = designProperties(design)
    for (id, value) in properties:
        if id == property:
            return value
    return None

def isFleet(id):
    '''
    Returns True if the object with the given id is a fleet and False otherwise.
    '''
    return id in fleets()

def isMyFleet(id):
    '''
    Returns True if the object with the given id is a fleet owned by you and False otherwise.
    '''
    return id in myFleets()
   
def shipsOfFleet(fleetid):
    '''
    Returns a list of ships of the fleet with the given id. [(something,design,numberOfUnits),...]
    '''
    global cache
    return cache.objects[fleetid].Ships[0][0]

def printProperties():
    '''
    Prints all existing properties. (id, name, description)
    '''
    global cache
    for property in cache.properties.values():
        print property.id, property.name, "(" + property.description + ")"    

def deleteAllMessages():
    '''
    Deletes all messages.
    '''
    global cache
    global connection
    
    for node in cache.messages[0]:
        if node == None:
            break
        evt = cache.apply("messages", "remove", 0, node, None)
        tp.client.cache.apply(connection, evt, cache)
