from daneel.common import Game as Cg
import logging
import tp.client.cache
from tp.netlib.objects import OrderDescs

class Game(Cg):

    def init(self,cache,daneel_engine,connection):
        pass

    def startTurn(self,cache,daneel_engine):
            daneel_engine.reset()
            Cg.startTurn(self,cache,daneel_engine)
            daneel_engine.activate('rfts_bc')


    def endTurn(self,cache,daneel_engine,connection):
        try:
            with daneel_engine.prove_n('parsec', 'turn', (), 1) as gen:
                for ((num), plan) in gen:
                    try:
                        plan()
                    except:
                        pass
        except:
            pass
        
        try:
            with daneel_engine.prove_n('parsec', 'orders_colonise', (), 2) as gen:
                for ((ship, planet), noplan) in gen:
                    logging.getLogger("ORD_COL").info("Colonising %s with %s" % (planet, ship))
                    order = findOrderDesc("Colonise")
                    args = [0, ship, -1, order.subtype, 0, [], planet]
                    o = order(*args)
                    try:
                        evt = cache.apply("orders","create after",ship,cache.orders[ship].head,o)
                        if connection != None:
                            tp.client.cache.apply(connection,evt,cache)
                    except:
                        logging.getLogger("ORD_FAL").warning("ORDER FAILED: Colonising %s with %s" % (planet, ship))
        except:
            pass
        try:
            with daneel_engine.prove_n('parsec', 'orders_move', (), 2) as gen:
                for ((ship, planet), noplan) in gen:
                    logging.getLogger("ORD_MVE").info("Moving %s to %s" % (ship, planet))
                    order = findOrderDesc("Move")
                    args = [0, ship, -1, order.subtype, 0, [], planet]
                    o = order(*args)
                    try:
                        evt = cache.apply("orders","create after",ship,cache.orders[ship].head,o)
                        if connection != None:
                            tp.client.cache.apply(connection,evt,cache)
                    except:
                        logging.getLogger("ORD_FAL").info("ORDER FAILED: Moving %s to %s" % (ship, planet))

        except:
            pass

        try:
            with daneel_engine.prove_n('parsec', 'orders_build', (), 2) as gen:
                for ((planet, ship_type), noplan) in gen:
                    if noplan != None:
                        noplan()
                    order = findOrderDesc("Build Fleet")
                    ship, name = parse_ship(ship_type)
                    logging.getLogger("ORD_BLD").info("Planet %s building %s ship" % (planet, name))
                    args = [0, planet, -1, order.subtype, 0, [], [[],ship], (len(name),name)]
                    o = order(*args)
                    try:
                        evt = cache.apply("orders","create after",planet,cache.orders[planet].head,o)
                        if connection != None:
                            tp.client.cache.apply(connection,evt,cache)
                    except:
                        logging.getLogger("ORD_FAL").info("ORDER FAILED: Planet %s building %s ship" % (planet, name))

        except:
            pass

        try:
            with daneel_engine.prove_n('parsec', 'orders_produce', (), 2) as gen:
                for ((planet, product_type), noplan) in gen:
                    order = findOrderDesc("Produce")
                    product, product_name = parse_product(product_type)
                    logging.getLogger("ORD_PRD").info("Planet %s producing %s" % (planet, product_name))
                    args = [0, planet, -1, order.subtype, 0, [], [[],product]]
                    o = order(*args)
                    try:
                        evt = cache.apply("orders","create after",planet,cache.orders[planet].head,o)
                        if connection != None:
                            tp.client.cache.apply(connection,evt,cache)
                    except:
                        logging.getLogger("ORD_FAL").info("ORDER FAILED: Planet %s producing %s" % (planet, product_name))

        except:
            pass

        logging.getLogger("DONETRN").info("Finished ordering moves")
        return


def findOrderDesc(name):
    name = name.lower()
    for d in OrderDescs().values():
        if d._name.lower() == name:
            return d

def parse_ship((ship_id,num)):
    ship_tup = {}
    ship_name = {}
    ship_tup[0] = list(((1,num),))
    ship_name[0] = "Scouting"
    #FIXME HARDCODING OF 5
    ship_tup[1] = list(((3,num),))
    ship_name[1] = "Colonization"

    return ship_tup[ship_id], ship_name[ship_id]    

def parse_product(product_id):
    product_tup = {}
    product_name = {}
    product_tup[0] = ((7,1),)
    product_name[0] = "Colonists"

    return product_tup[product_id], product_name[product_id]

