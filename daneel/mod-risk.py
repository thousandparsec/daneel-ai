import logging
import tp.client.cache
from tp.netlib.objects import OrderDescs
from constraint import *
from problem import *
import sys

constraints = """adjacent(int,int)*
reinforcements(int)
armies(int,int)
order_move(int,int,int)
order_reinforce(int,int)
order_colonise(int,int)""".split('\n')

rules = """adjacentset @ adjacent(A,B) \ adjacent(A,B) <=> pass
addarmies @ resources(P,1,N,_) ==> armies(P,N)""".split('\n')

debug = 1

def init(cache,rulesystem,connection):

    planets, systems, adjacent = {}, {}, []
    planet_list = []
    
    rulesystem.setConstant('liststr', ['SingleList'])
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
    r = rulesystem.getConstant('adjacent_planets')
    dict = {}
    ll = []
    for (P,P2) in r:
        iter = []
        try:
            dict[P]
        except KeyError:
            for (P1,P12) in r:
                if P == P1:
                    iter.append(P12)
                else:
                    pass
            dict[P] = True
            # ll.append(iter.append(P))
            ll.append({P: list(set(iter))})
        except:
            pass
                    
    rulesystem.setConstant("adj_list", ll)            
    return


def startTurn(cache,daneelproblem, delta = 0):
    liststr = daneelproblem.getConstant('liststr')[0]
    
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
                save_syntax ={'objects': ['id', 'resources']})
    
    if(debug):
        myplanets.setsol([{'id': 23, 'resources': [(1, 3, 30, 0)]},{'id': 15, 'resources': [(1, 3, 30, 0)]}, {'id': 21, 'resources': [(1, 3, 30, 0)]}])
    
    daneelproblem.addVariableRule({myplanets.getName(): myplanets})
    if myplanets.getsol() == []:
        logging.getLogger("daneel.mod-risk").warning("No owned planets found. We're dead, Jim.")
        return

    func = lambda objects,whoami: neutralPlanets(objects,whoami)
    neutralplanets = Rule(store= daneelproblem, 
                name='neutralplanets', 
                vars=[{'varname': 'whoami', 'type':'variable'}, {'varname': 'objects', 'type':'variable'}], 
                cons=[{'func': func, 'func_vars': func_vars}],
                save_syntax ={'objects': 'id'})
    daneelproblem.addVariableRule({neutralplanets.getName(): neutralplanets})
     
    func = lambda objects,whoami: enemyPlanets(objects,whoami)
    enemyplanets = Rule(store= daneelproblem, 
                name='enemyplanets', 
                vars=[{'varname': 'whoami', 'type':'variable'}, {'varname': 'objects', 'type':'variable'}], 
                cons=[{'func': func, 'func_vars': func_vars}],
                save_syntax ={'objects': ['id', 'resources']})
    daneelproblem.addVariableRule({enemyplanets.getName(): enemyplanets})
    
    func = lambda myplanets,adj_list: safePlanets(myplanets,adj_list)
    func2 = lambda adj_list, myplanets: allValsInList(adj_list, myplanets)
    func_vars = ['myplanets', 'adj_list']
    func_vars2 = ['adj_list', 'myplanets' + liststr]
    safeplanets = Rule(store= daneelproblem, 
                name='safeplanets', 
                vars=[{'varname': 'myplanets', 'type':'variable'}, {'varname': 'adj_list', 'type':'constant'},
                      {'varname': 'myplanets', 'type':'variable', 'list': True}], 
                cons=[{'func': func, 'func_vars': func_vars}
                      , 
                      {'func': func2, 'func_vars': func_vars2}
                      ],
                save_syntax ={'myplanets': True})
    daneelproblem.addVariableRule({safeplanets.getName(): safeplanets})
    print "SAFE", safeplanets.getsol()
    
    inc = lambda a,b: a + b
    
    if(debug):
        myplanets.setsol([{'id': 23, 'resources': [(1, 3, 30, 0)]},{'id': 15, 'resources': [(1, 3, 30, 0)]}, {'id': 21, 'resources': [(1, 3, 30, 0)]}])
    
    init = []    
    needed = convert_domain(daneelproblem, init, myplanets.getsol(), {'single': True, 'change': {'resources': 1, 'new_node': 3}})
    

    if(debug):
        myplanets.setsol([{'myplanets': {'id': 23, 'resources': [(1, 3, 30, 0)]}, 'score': 1, 'extra': 3},
                          {'myplanets': {'id': 21, 'resources': [(1, 3, 30, 0)]}, 'score': 2},
                          {'myplanets': {'id': 15, 'resources': [(1, 3, 30, 0)]}, 'score': 3}
                          ])
    
    init = []
    needed = convert_domain(daneelproblem, init, myplanets.getsol(), {'val': 'myplanets', 
    'change': {'resources': {'func':inc, 'args': [2, {'name': 'resources', 'node': [0,2]}]}, 'new_node': 3, 'id': {'func': inc, 'args': [22,{'name': 'id'}]}}}, 
                                                                                                                                         {'val': 'score', 'change': 77})
    print needed    
    sys.exit()
    return

def convert_domain(store, init,  ll, *args):
    for dict in ll:
        new_dict = {}
        for arg in args:
 #           print "ARG", arg
            if hasattr(dict, 'items'):
                for (k,v) in dict.items():
                    if hasattr(v, 'items'):
                        for (k2, v2) in v.items():
                            try:
                                if new_dict[k2]:
                                    pass
                            except:
                                new_dict[k2] = v2
                            
                       # print new_dict
                    else:
                        new_dict[k] = v
                    
                    fail = 0
                    try:    
                        if arg['val'] == k:
                            pass
                    except:
                        fail += 1
                        
                    try:
                        if arg['single'] == True:
                            pass
                    except:
                        fail += 1
                        
        #                    print "MATCH", k, v, arg
                    if ( fail < 2):        
                        if hasattr(arg['change'], 'items'):
                            for (k1,v1) in arg['change'].items():
                                try:
                                    if hasattr(v1, 'items'):
                                        func = v1['func']
                                        node_list = []
                                        try:
                                            if v[k1]:
                                                for node in v1['args']:
                                                    if hasattr(node, 'items'):
                                                        nn = new_dict[node['name']]
                                                        try:
                                                            subnode = node['node']
                                                            for item in subnode:
                                                                nn = nn[item]
                                                            
                                                            node_list.append(nn)
                                                        except:
                                                            node_list.append(nn)
                                                            pass
                                                    else:
                                                        node_list.append(node)
                                                
                                                new_dict[k1] = func(*node_list)
                                                
                                        except:
                                            pass                                        
                                    else:
                                        pass
                                except:
                                    pass
                        else:
                            pass
                    else:
                        pass
            else:
                pass
                    
        init.append(new_dict)
    print init                
    return init

def allValsInList(x,y):
    x = x.values()[0]
    for item in x:
        if item in [i['id'] for i in y]:
            pass
        else:
            return False
    return True


    #myplanet = selectOwnedPlanet(cache)
#    if myplanet is None:
 #       logging.getLogger("daneel.mod-risk").warning("No owned planets found. We're dead, Jim.")
  #      return
  #  v = cache.objects[myplanet]
   # store.addConstraint("reinforcements(%i)"%v.resources[0][2])

def endTurn(cache,rulesystem,connection):
    return
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
    
def neutralPlanets(object, player_id):
    if not (myObject(-1, object)):
        return False
    if not (isPlanet(object)):
        return False
    else:
        return True

def enemyPlanets(object, player_id):
    if myObject(player_id, object):
        return False
    if myObject(-1, object):
        return False
    if not (isPlanet(object)):
        return False
    else:
        return True
    

def safePlanets(myplanet, adjacent_pair):
    if myplanet['id'] != adjacent_pair.keys()[0]:
        return False
    else:
        print myplanet['id'], adjacent_pair.keys()[0]
        return True
"""
def inList(item, list):
    list = list.values()
    if item in list:
        return True
    else:
        return False
"""
