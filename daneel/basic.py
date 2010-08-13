from tp.netlib.objects import OrderDescs
from tp.client.objectutils import getResources

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

argumentTypeNames = {0:"Absolute Space Coordinates", 1:"Time", 2:"Object", 3:"Player", 4:"Relative Space Coordinates", 5:"Range", 6:"List", 7:"String", 8:"Generic Reference", 9:"Generic Reference List"}

def getLastTurnTime(cache, delta=0):
    if delta == 0:
        return - 1
    else:
        latest_time = cache.objects.times[0]
        for (num, time) in cache.objects.times.iteritems():
            if time > latest_time:
                latest_time = time
            else:
                pass
        return latest_time

#TODO: this should do the more general things TP04 describes, not the specifics of TP03
def startTurn(cache, store, delta=0):
    #last_time = getLastTurnTime(cache,delta)       
    for (k, v) in cache.players.items():
        if k != 0:
            store.addConstraint("player(%i,%s)" % (k, v.name))
        
    store.addConstraint("whoami(%i)" % cache.players[0].id)
    store.addConstraint("turn(%i)" % cache.objects[0].Informational[0][0])
    for (k, v) in cache.objects.items():
#   this is in no way optimal but at least it holds all the data     
#        if delta and cache.objects.times[k] < last_time:
#            pass
#        else:
        store.addConstraint("subtype(%i,%i)" % (k, v.subtype))
        #Null this prevents errors when there is a semicolon in the name and when the name is empty
        if v.name == "":
            store.addConstraint("name(%i,%s)" % (k, "no name"))
        else:
            store.addConstraint("name(%i,%s)" % (k, v.name.replace(",", "'")))
        store.addConstraint("size(%i,%i)" % (k, v.size))
        if hasattr(v.Positional, "Position"):
            store.addConstraint("pos(%i,%i,%i,%i)" % ((k, v.Positional.Position.vector.x, v.Positional.Position.vector.y, v.Positional.Position.vector.z)))
        if hasattr(v.Positional, "Velocity"):
            store.addConstraint("vel(%i,%i,%i,%i)" % ((k, v.Positional.Velocity.vector.x, v.Positional.Velocity.vector.y, v.Positional.Velocity.vector.z)))
        for child in v.contains:
            store.addConstraint("contains(%i,%i)" % (k, child))
        if hasattr(v, "Ownership"):
            store.addConstraint("owner(%i,%i)" % (k, v.Ownership.Owner.id))
        for res in getResources(cache,k):
            store.addConstraint("resources(%i,%i,%i,%i,%i)" % ((k,) + res))
        if hasattr(v, "ships"):
            for (t, num) in v.ships:
                store.addConstraint("ships(%i,%i,%i)" % (k, t, num))
        if hasattr(v, "damage"):
            store.addConstraint("damage(%i,%i)" % (k, v.damage))
        if hasattr(v, "start"):
            store.addConstraint("start(%i,%i,%i,%i)" % ((k,) + v.start))
        if hasattr(v, "end"):
            store.addConstraint("end(%i,%i,%i,%i)" % ((k,) + v.end))

def init(cache, rulesystem, connection):
    #printPossibleOrders(cache)
    #printPossibleOrdersCode(cache)
    return
   

def printPossibleOrders(cache):
    ''' Prints possible orders and their arguments with descriptions.
     List of orders is send by the server.
     NOTE: argument types may be wrong (as I don't understand them yet) '''
     
    global argumentTypeNames
    print "LIST OF POSSIBLE ORDERS\n"
    orderList = OrderDescs()
    
    
    for i in range(len(orderList)):
        tempOrder = orderList[i]
        print "Name:", tempOrder._name
        print "Code:", tempOrder.subtype 
        print "Desc:", tempOrder.doc
        argumentStringList = []
        argumentList = tempOrder.packet.arguments
        for arg in argumentList:
            argumentStringList += [ "Arg name: " + arg[0] + "    Arg type: " + argumentTypeNames[arg[1]] + " (code:" + str(arg[1]) + ")    Arg desc: " + arg[2]]
        if argumentStringList == []:
            print "No arguments"
        else:
            print "Arguments:", "\n", "\n".join(argumentStringList), "\n"
        print
    print "END OF LIST OF POSSIBLE ORDERS\n"

def printPossibleOrdersCode(cache):
    ''' Prints code for possible orders and their arguments with descriptions.
     List of orders is send by the server.
     NOTE: argument types may be wrong (as I don't understand them yet) '''
     
    global argumentTypeNames
    print "LIST OF POSSIBLE ORDERS CODE\n"
    orderList = OrderDescs()
    
    #constraint generation
    import sys
    print """import logging
import tp.client.cache
from tp.netlib.objects import OrderDescs
import extra.objectutils
import helper

rulesystem = None"""
    print 
    sys.stdout.write("constraints = \"\"\"")
    for i in range(len(orderList)):
        tempOrder = orderList[i]
        argumentList = tempOrder.packet.arguments 
        #the name of the order constraint (with _ instead of spaces)
        constraintString = "order_" + tempOrder._name.replace(" ", "_").lower() + "("
        #the arguments for the constraint (with , in between)
        constraintString += ",".join(["int"] + [argumentToStringForConstraint(arg) for arg in argumentList]) + ")"
        print constraintString
    print "order_none(int)\"\"\".split(\'\\n\')"
    print
    print "def endTurn(cache, rs, connection):"
    print "    global rulesystem"
    print "    #update globals"
    print "    rulesystem = rs"
    print "    cache = cache2"
    print "    helper.rulesystem = rulesystem"
    print "    helper.cache = cache"
    print "    "
    print "    AICode()"
    for i in range(len(orderList)):
        tempOrder = orderList[i]
        print "    executeOrders" + pascalCase(tempOrder._name) + "(cache, connection)"
    
    
    print
    #order function call generation
    for i in range(len(orderList)):
        tempOrder = orderList[i]
        argumentList = tempOrder.packet.arguments
        argumentStringList = []
        for arg in argumentList:
            argumentStringList += [ "Arg name: " + arg[0] + "    Arg type: " + argumentTypeNames[arg[1]] + " (code:" + str(arg[1]) + ")    Arg desc: " + arg[2]]
        
        #the name of the order (in camel case)
        functionString = "order" + pascalCase(tempOrder._name) + "(id"
        #the arguments for the function (same as the constraint)
        for arg in argumentList:
            functionString += ", " + arg[0].lower()
        functionString += "):"
        functionCommentStringList = argumentStringList 
        print "def " + functionString
        print "    '''"
        print "    " + tempOrder.doc
        print "    id is for the object the order is for"
        for comment in functionCommentStringList:
            print "    ", comment
        print "    '''"
        print "    global rulesystem"    
        sys.stdout.write("    rulesystem.addConstraint(\"order_" + tempOrder._name.replace(" ", "_").lower() + "(\" + str(id)")
        for x in argumentList:
            sys.stdout.write(" + \", \"" + argumentToStringForFunction(x))
        print " + \")\")"
        print "    return"
        print
    
    #order removing function    
    print "def orderNone(id):"
    print "    \'\'\'"
    print "    Removes orders from the object."
    print "    \'\'\'"
    print "    global rulesystem"
    print "    rulesystem.addConstraint(\"order_none(\" + str(id) + \")\")"
    print "    return"
    print
    print "def executeOrdersNone(cache, connection):"
    print "    global rulesystem"
    print "    orders = rulesystem.findConstraint(\"order_none(int)\")"
    print "    for orderConstraint in orders:"
    print "        executeOrder(cache, connection, objectId, None)"
    print
    
    #order function execution generation
    for i in range(len(orderList)):
        tempOrder = orderList[i]
        argumentList = tempOrder.packet.arguments
        #the name of the order constraint (with _ instead of spaces)
        constraintString = "order_" + tempOrder._name.replace(" ", "_").lower() + "("
        #the arguments for the constraint (with , in between)
        constraintString += ",".join(["int"] + [argumentToStringForConstraint(arg) for arg in argumentList]) + ")"
        
        print "def executeOrders" + pascalCase(tempOrder._name) + "(cache, connection):"
        print "    global rulesystem"
        print "    orders = rulesystem.findConstraint(\"" + constraintString + "\")"
        print "    for orderConstraint in orders:"
        print "        args = orderConstraint.args"
        print "        objectId = int(args[0])"
        offset = 1
        for arg in argumentList:
            transformationString, offset = argumentTransformarion(arg, offset)
            print "        " + transformationString
        print "        ordertype = findOrderDesc(\"" + tempOrder._name + "\")"
        sys.stdout.write("        args = [0, objectId, -1, ordertype.subtype, 0, []")
        for arg in argumentList:
            sys.stdout.write(", " + pascalCase(arg[0]))
        print "]"
        print "        order = ordertype(*args)"
        print "        executeOrder(cache, connection, objectId, order)"
        print
    
    #order execution code and some helper functions
    print """def executeOrder(cache, connection, objectId, order):
    # get the queue for the object
    queueid = extra.objectutils.getOrderQueueList(cache, objectId)[0][1]
    queue = cache.orders[queueid]
    node = queue.first
    
    #check if there is no existing order
    if order != None and queue.first.CurrentOrder is None:
        # make a new order   
        evt = cache.apply(\"orders\", \"create after\", queueid, node, order)
        tp.client.cache.apply(connection, evt, cache)
    #check if the existing order is the same as current order
    elif not checkIfOrdersSame(node.CurrentOrder, order):
        if order != None:
            #replace the current order with the new one
            evt = cache.apply(\"orders\", \"change\", queueid, node, order)
            tp.client.cache.apply(connection, evt, cache)
        #delete order
        else:
            nodes = [x for x in queue]
            evt = cache.apply(\"orders\", \"remove\", queueid, nodes=nodes)
            tp.client.cache.apply(connection, evt, cache)

def checkIfOrdersSame(order1, order2):
    #check if both are None
    if order1 is None and order2 is None:
        return True
    
    #check the type
    if type(order1) != type(order2):
        return False
    #check the name
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

def AICode():
    #TODO your AI code comes here
    return"""
    
    
    print "END OF LIST OF POSSIBLE ORDERS CODE\n"
    
def pascalCase(string):
    '''
    ConvertsTextToPascalCase
    '''
    return "".join([word[0].upper() + word[1:] for word in string.split(" ")])

def camelCase(string):
    '''
    convertsTextToCamelCase
    '''
    string = pascalCase(string)
    string = string[0].lower() + string[1:] 
    return string

def argumentToStringForConstraint(arg):
    #swich by argument type
    if arg[1] == 0: #Absolute Space Coordinates
        return "int,int,int"
    if arg[1] == 1: #Time
        return "int"
    if arg[1] == 2: #object
        return "int"
    if arg[1] == 3: #Player
        return "int"
    if arg[1] == 4: #Relative Space Coordinates
        return "int,int,int,int"
    if arg[1] == 5: #range
        return "int" #prbobably int
    if arg[1] == 6: #list
        return "list" 
    if arg[1] == 7: #string
        return "str"
    return None


def argumentToStringForFunction(arg):
    #swich by argument type
    if arg[1] == 0: #Absolute Space Coordinates
        return " + str(" + camelCase(arg[0]) + "[0]) + \",\" + str(" + camelCase(arg[0]) + "[1])""+\",\" + str(" + camelCase(arg[0]) + "[2])"
    if arg[1] == 1: #Time
        return " + str(" + camelCase(arg[0]) + ")"
    if arg[1] == 2: #object
        return " + str(" + camelCase(arg[0]) + ")"
    if arg[1] == 3: #Player
        return " + str(" + camelCase(arg[0]) + ")"
    if arg[1] == 4: #Relative Space Coordinates
        return " + str(" + camelCase(arg[0]) + "[0]) + \",\" + str(" + camelCase(arg[0]) + "[1])""+\",\" + str(" + camelCase(arg[0]) + "[2])""+\",\" + str(" + camelCase(arg[0]) + "[3])"
    if arg[1] == 5: #range
        return " + str(" + camelCase(arg[0]) + ")"
    if arg[1] == 6: #list
        return " + str(" + camelCase(arg[0]) + ")" 
    if arg[1] == 7: #string
        return " + " + camelCase(arg[0])
    return None

def argumentTransformarion(arg, offset):
    #swich by argument type
    if arg[1] == 0: #Absolute Space Coordinates
        return camelCase(arg[0]) + " = [[int(args[" + str(offset) + "]), int(args[" + str(offset + 1) + "]), int(args[" + str(offset + 2) + "])]]", offset + 3
    if arg[1] == 1: #Time
        return camelCase(arg[0]) + " = int(args[" + str(offset) + "])" , offset + 1
    if arg[1] == 2: #object
        return camelCase(arg[0]) + " = int(args[" + str(offset) + "])" , offset + 1
    if arg[1] == 3: #Player
        return camelCase(arg[0]) + " = int(args[" + str(offset) + "])" , offset + 1
    if arg[1] == 4: #Relative Space Coordinates
        return camelCase(arg[0]) + " = [[int(args[" + str(offset) + "]), int(args[" + str(offset + 1) + "]), int(args[" + str(offset + 2) + "]), int(args[" + str(offset + 3) + "])]]", offset + 4
    if arg[1] == 5: #range
        return camelCase(arg[0]) + " = int(args[" + str(offset) + "])" , offset + 1
    if arg[1] == 6: #list
        return camelCase(arg[0]) + " = [[], args[" + str(offset) + "]]" , offset + 1
    if arg[1] == 7: #string
        return camelCase(arg[0]) + " = [len(args[" + str(offset) + "]), args[" + str(offset) + "]]", offset + 1
    return None, None
