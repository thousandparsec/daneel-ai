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
    orders_build_fleet = []
    orders_produce = []
    orders_move = []
    orders_colonise = []
    
    func = lambda objects,whoami: myPlanets(objects,whoami)
    func_vars = ['objects', 'whoami']
    myplanets = Rule(store= daneelproblem, 
                name='myplanets', 
                vars=[{'varname': 'whoami', 'type':'variable'}, {'varname': 'objects', 'type':'variable'}], 
                cons=[{'func': func, 'func_vars': func_vars}],
                save_syntax ={'objects': True})
    
    daneelproblem.addVariableRule({myplanets.getName(): myplanets})
    
    func = lambda objects,whoami: otherPlanets(objects,whoami)
    func_vars = ['objects', 'whoami']
    otherplanets = Rule(store= daneelproblem, 
                name='otherplanets', 
                vars=[{'varname': 'whoami', 'type':'variable'}, {'varname': 'objects', 'type':'variable'}], 
                cons=[{'func': func, 'func_vars': func_vars}],
                save_syntax ={'objects': True})
    
    daneelproblem.addVariableRule({otherplanets.getName(): otherplanets})
   
    func = lambda object: isStar(object)
    func_vars =['objects']    
    stars = Rule(store = daneelproblem,
                 name='stars',
                 vars=[{'varname': 'objects', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}],
                 save_syntax ={'objects': True})
    
    daneelproblem.addVariableRule({stars.getName(): stars})
    
    func = lambda object: isScoutShip(object)
    func_vars =['objects']    
    scouts = Rule(store = daneelproblem,
                 name='scouts',
                 vars=[{'varname': 'objects', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}],
                 save_syntax ={'objects': True})
    
    daneelproblem.addVariableRule({scouts.getName(): scouts})
    
    func = lambda object: isColonyShip(object)
    func_vars =['objects']    
    colonyships = Rule(store = daneelproblem,
                 name='colonyships',
                 vars=[{'varname': 'objects', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}],
                 save_syntax ={'objects': True})
    
    daneelproblem.addVariableRule({colonyships.getName(): colonyships})
    
    # TODO: ORDER SELECTION STILL INCOMPLETE
    
    num_stars = len(stars.getsol())
    if ( num_stars > 10):
        for planet in myplanets.getsol():
            print planet
            node = {'planet': planet['id'], 'type': [(1,1)], 'str': 'Scouting', 'item': planet}
            orders_build_fleet.append(node)
    
    for item in myplanets.getsol():
        node = {'planet': item['id'], 'type': ((7,1),)}
        orders_produce.append(node)
    
    daneelproblem.addVariableRule({'orders_produce': orders_produce})
    
    
    for item in myplanets.getsol():
        for resource_node in item['resources']:
            if resource_node[0] == 7 and resource_node[1] >= 5:
                node = {'planet': item['id'], 'type': ((3,resource_node[1]),), 'str': 'Colonization', 'item': item}
                orders_build_fleet.append(node)
            else:
                pass
    
    daneelproblem.addVariableRule({'orders_build_fleet': orders_build_fleet})
    
    
    func = lambda star,planet,colonyship: validColonise(star,planet,colonyship)
    func_vars =['stars','otherplanets', 'colonyships']    
    valid_colonies = Rule(store = daneelproblem,
                 name='valid_colonies',
                 vars=[{'varname': 'otherplanets', 'type':'variable'}, {'varname': 'stars', 'type':'variable'},
                        {'varname': 'colonyships', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}])

    
    daneelproblem.addVariableRule({valid_colonies.getName(): valid_colonies})

    if valid_colonies.getsol() != None:
        for item in valid_colonies.getsol():
            node = {'fleet': item['colonyships']['id'], 'planet': item['otherplanets']['id']}
            orders_colonise.append(node)

    daneelproblem.addVariableRule({'orders_colonise': orders_colonise})
        
    func = lambda planet,colonyship: ColonyDest(planet,colonyship)
    func_vars =['otherplanets', 'colonyships']    
    colony_destinations = Rule(store = daneelproblem,
                 name='colony_destinations',
                 vars=[{'varname': 'otherplanets', 'type':'variable'}, {'varname': 'colonyships', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}])
    
    daneelproblem.addVariableRule({colony_destinations.getName(): colony_destinations})

    col_d = []
    if colony_destinations.getsol() != None:
        for item in colony_destinations.getsol():
            node = {'fleet': item['colonyships']['id'], 'planet': item['otherplanets']['id']}
            col_d.append(node)
    orders_move.extend(best(col_d, 'fleet', 'planet'))

             
    func = lambda star,scoutship: ScoutLocations(star,scoutship)
    func_vars =['stars', 'scouts']    
    scout_locations = Rule(store = daneelproblem,
                 name='scout_locations',
                 vars=[{'varname': 'stars', 'type':'variable'}, {'varname': 'scouts', 'type':'variable'}],
                 cons=[{'func': func, 'func_vars': func_vars}])
    
    daneelproblem.addVariableRule({scout_locations.getName(): scout_locations})
    
    scouts_l = []   
    if scout_locations.getsol() != None:
        for item in scout_locations.getsol():
            node = {'fleet': item['scouts']['id'], 'planet': item['stars']['id']}
            scouts_l.append(node)

    orders_move.extend(best(scouts_l, 'fleet', 'planet') )
    daneelproblem.addVariableRule({'orders_move': orders_move})
                   
    return
    
# FIXME
def best(list_l, subject, object):
    orders = []
    orders_index = []
    orders_object = []
    for item in list_l:
        if item[subject] not in orders_index and item[object] not in orders_object:
            orders.append(item)
            orders_index.append(item[subject])
            orders_object.append(item[object])
        else:
            pass
    
    return orders

def info(problem):
    turn = problem.getVariableRuleSolutions('turn')
    logging.getLogger("TURN").info('The turn is %s', turn[0])   


def ScoutLocations(star,scout):
    if not(isStar(star)):
        return False
    if not(isScoutShip(scout)):
        return False

    return True



def ColonyDest(planet,colonyship):
    if not(isPlanet(planet)):
        return False
    if not(isColonyShip(colonyship)):
        return False

    return True


def validColonise(star,planet,colonyship):
    if not(isStar(star)):
        return False
    if star['contains'] == []:
        return False

    
    if planet['id'] in star['contains'] and colonyship['id'] in star['contains']:
        return True
    else:
        return False
    
        

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

def otherPlanets(object, player_id):
    if myObject(player_id, object):
        return False
    if not (isPlanet(object)):
        return False
    else:
        return True

     
     
def endTurn(cache,rulesystem,connection):
    print "e1"
    orders = rulesystem.getVariableRule("orders_move")
    for order in orders:
        objid = order['fleet']
        destination = order['planet']
        logging.getLogger("ORD_MVE").info("Moving %s to %s" % (objid,cache.objects[destination].pos))
        moveorder = findOrderDesc("Move")
        args = [0, objid, -1, moveorder.subtype, 0, [], destination]
        order = moveorder(*args)
        evt = cache.apply("orders","create after",objid,cache.orders[objid].head,order)
        if connection != None:
            tp.client.cache.apply(connection,evt,cache)
    print "e2"
    orders = rulesystem.getVariableRule("orders_build_fleet")
    for order in orders:
        objid = order['planet']
        ships = list(order['type'])
        name = order['str']
        logging.getLogger("ORD_BLD").info("Planet %d Ordering fleet %s of %s" % (objid,name,ships))
        buildorder = findOrderDesc("Build Fleet")
        args = [0, objid, -1, buildorder.subtype, 0, [], [[],ships], (len(name),name)]
        order = buildorder(*args)
        evt = cache.apply("orders","create after",objid,cache.orders[objid].head,order)
        if connection != None:
            tp.client.cache.apply(connection,evt,cache)
    print "e3"
    orders = rulesystem.getVariableRule("orders_produce")
    for order in orders:
        objid = order['planet']
        toproduce = order['type']
        logging.getLogger("ORD_PRD").info("Producing %s" % toproduce)
        order = findOrderDesc("Produce")
        args = [0, objid, -1, order.subtype, 0, [], [[],toproduce]]
        o = order(*args)
        evt = cache.apply("orders","create after",objid,cache.orders[objid].head,o)
        if connection != None:
            tp.client.cache.apply(connection,evt,cache)
    print "e4"
    try:    
        orders = rulesystem.getVariableRule("orders_colonise")
        for order in orders:
            objid = order['fleet']
            target = order['planet']
            logging.getLogger("ORD_PRD").info("Colonizing %s" % target)
            order = findOrderDesc("Colonise")
            args = [0, objid, -1, order.subtype, 0, [], target]
            o = order(*args)
            evt = cache.apply("orders","create after",objid,cache.orders[objid].head,o)
            if connection != None:
                tp.client.cache.apply(connection,evt,cache)
    except:
        pass


def findOrderDesc(name):
    name = name.lower()
    for d in OrderDescs().values():
        if d._name.lower() == name:
            return d
