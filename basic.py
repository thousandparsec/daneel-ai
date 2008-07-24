import tp.client.cache
from tp.netlib.objects import OrderDescs

constraints = """subtype(int,int)
name(int,unicode)
size(int,int)
pos(int,int,int,int)
vel(int,int,int,int)
contains(int,int)
owner(int,int)
resources(int,int,int,int,int)
whoami(int)
turn(int)
fleet(int)
planet(int)
star(int)
order_move(int,int)
order_buildfleet(int,tuple,str)
order_produce(int,tuple)
order_colonise(int,int)
cacheentered""".split('\n')

rules = """fleettype @ subtype(X,4) ==> fleet(X)
planettype @ subtype(X,3) ==> planet(X)
startype @ subtype(X,2) ==> star(X)""".split('\n')

def startTurn(cache,store):
    store.addConstraint("whoami(%i)" % cache.players[0].id)
    store.addConstraint("turn(%i)"%cache.objects[0].turn)
    for (k,v) in cache.objects.items():
        store.addConstraint("subtype(%i,%i)"%(k,v.subtype))
        store.addConstraint("name(%i,%s)"%(k,v.name))
        store.addConstraint("size(%i,%i)"%(k,v.size))
        store.addConstraint("pos(%i,%i,%i,%i)"%((k,) + v.pos))
        store.addConstraint("vel(%i,%i,%i,%i)"%((k,) + v.vel))
        for child in v.contains:
            store.addConstraint("contains(%i,%i)"%(k,child))
        if hasattr(v,"owner"):
            store.addConstraint("owner(%i,%i)"%(k,v.owner))
        if hasattr(v,"resources"):
            for res in v.resources:
                store.addConstraint("resources(%i,%i,%i,%i,%i)"%((k,)+res))
    store.addConstraint("cacheentered")

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