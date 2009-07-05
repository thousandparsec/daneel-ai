import tp.client.cache
from tp.netlib.objects import OrderDescs
import sys
from constraint import *
import logging

constraints = """player(int,unicode)
subtype(int,int)
name(int,unicode)
size(int,int)
pos(int,int,int,int)
vel(int,int,int,int)
contains(int,int)
universe(int)
galaxy(int)
star(int)
planet(int)
fleet(int)
wormhole(int)
start(int,int,int,int)
end(int,int,int,int)
owner(int,int)
resources(int,int,int,int,int)
whoami(int)
turn(int)
ships(int,int,int)
damage(int,int)
cacheentered""".split('\n')

rules = """universetype @ subtype(X,0) ==> universe(X)
galaxytype @ subtype(X,1) ==> galaxy(X)
startype @ subtype(X,2) ==> star(X)
planettype @ subtype(X,3) ==> planet(X)
fleettype @ subtype(X,4) ==> fleet(X)
wormholetype @ subtype(X,5) ==> wormhole(X)""".split('\n')

def getLastTurnTime(cache,delta=0):
    if delta == 0:
        return -1
    else:
        latest_time = cache.objects.times[0]
        for (num,time) in cache.objects.times.iteritems():
            if time > latest_time:
                latest_time = time
            else:
                pass
        return latest_time
    
def startTurn(cache,store,delta=0):
    player, whoami,turn,objects = [], [], [], []
    dict_of_lists = {'player': player, 'whoami': whoami, 'turn': turn, 'objects': objects}
    store_list = ['subtype', 'name', 'size', 'pos', 'vel', 'owner', 'contains', 'resources', 'ships', 'damage', 'start', 'end']

        
    last_time = getLastTurnTime(cache,delta)       
    for (k,v) in cache.players.items():      
        player.append ( (k, v.name) )
          
    whoami.append (cache.players[0].id)
    turn.append(cache.objects[0].turn)

        
    for (k,v) in cache.objects.items():
        element = {}
        if delta and cache.objects.times[k] < last_time:
            pass
        else:
                element['id'] = k
                element['time_modified'] = cache.objects.times[k]
                for variable in dir(v):
                    if variable == 'resources':
                        logging.getLogger('RESOURCES').debug( eval('v.resources[0][1]') )
                    if variable in store_list:
                        try:
                            element['%s' %variable.__str__()] = eval('v.%s' % variable)
                        except:
                            pass
                    else:
                        pass
                    
        objects.append( element)
    
    store.variableStoreAppend(dict_of_lists)

    return