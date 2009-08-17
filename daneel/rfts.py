from daneel.common import Game as Cg
import logging
import tp.client.cache
import daneel.util as util
import daneel.common as common


class Game(Cg):
    '''
    A simple port of the daneel-ai RFTS CHR system.
    '''
    def init(self,parsec):
        '''
        initialise
        '''
        Cg.init(self,parsec)
        return

    def startTurn(self,parsec):
        '''
        At the start of the turn we parse the cache
        '''
        parsec.daneel_engine.reset()
        Cg.startTurn(self,parsec)
        parsec.daneel_engine.activate(parsec.rulesfile)


    def endTurn(self,parsec):
        try:
            with parsec.daneel_engine.prove_n('parsec', 'turn', (), 1) as gen:
                for ((num), plan) in gen:
                    try:
                        plan()
                    except:
                        pass
        except:
            pass
        
        '''
        Search for colonise matches and try to do any matches
        '''
        try:
            with parsec.daneel_engine.prove_n('parsec', 'orders_colonise', (), 2) as gen:
                for ((ship, planet), noplan) in gen:
                    logging.getLogger("ORD_COL").info("Colonising %s with %s" % (planet, ship))
                    if parsec.pickled == False:
                        order = util.findOrderDesc("Colonise")
                        args = [0, ship, -1, order.subtype, 0, [], planet]
                        o = order(*args)
                        try:
                            evt = parsec.cache.apply("orders","create after",ship,parsec.cache.orders[ship].head,o)
                            if parsec.connection != None:
                                tp.client.cache.apply(parsec.connection,evt,parsec.cache)
                        except:
                            logging.getLogger("ORD_FAL").warning("ORDER FAILED: Colonising %s with %s" % (planet, ship))
        except:
            pass

        '''
        Search for moving orders and try to do any matches
        '''
        try:
            with parsec.daneel_engine.prove_n('parsec', 'orders_move', (), 2) as gen:
                for ((ship, planet), noplan) in gen:
                    logging.getLogger("ORD_MVE").info("Moving %s to %s" % (ship, planet))
                    if parsec.pickled == False:
                        order = util.findOrderDesc("Move")
                        args = [0, ship, -1, order.subtype, 0, [], planet]
                        o = order(*args)
                        try:
                            evt = parsec.cache.apply("orders","create after",ship,parsec.cache.orders[ship].head,o)
                            if parsec.connection != None:
                                tp.client.cache.apply(parsec.connection,evt,parsec.cache)
                        except:
                            logging.getLogger("ORD_FAL").info("ORDER FAILED: Moving %s to %s" % (ship, planet))

        except:
            pass

        '''
        Search for building orders and try to do any matches
        '''

        try:
            with parsec.daneel_engine.prove_n('parsec', 'orders_build', (), 2) as gen:
                for ((planet, ship_type), noplan) in gen:
                    if noplan != None:
                        noplan()
                    if parsec.pickled == False:
                        order = util.findOrderDesc("Build Fleet")
                        ship, name = parse_ship(ship_type)
                        logging.getLogger("ORD_BLD").info("Planet %s building %s ship" % (planet, name))
                        args = [0, planet, -1, order.subtype, 0, [], [[],ship], (len(name),name)]
                        o = order(*args)
                        try:
                            evt = parsec.cache.apply("orders","create after",planet,parsec.cache.orders[planet].head,o)
                            if parsec.connection != None:
                                tp.client.cache.apply(parsec.connection,evt,parsec.cache)
                        except:
                            logging.getLogger("ORD_FAL").info("ORDER FAILED: Planet %s building %s ship" % (planet, name))

        except:
            pass

        '''
        Search for production orders and try to do any matches
        '''

        try:
            with parsec.daneel_engine.prove_n('parsec', 'orders_produce', (), 2) as gen:
                for ((planet, product_type), noplan) in gen:
                    logging.getLogger("ORD_PRD").info("Planet %s producing %s" % (planet, product_name))
                    if parsec.pickled == False:
                        order = util.findOrderDesc("Produce")
                        product, product_name = parse_product(product_type)
                        args = [0, planet, -1, order.subtype, 0, [], [[],product]]
                        o = order(*args)
                        try:
                            evt = parsec.cache.apply("orders","create after",planet,parsec.cache.orders[planet].head,o)
                            if parsec.connection != None:
                                tp.client.cache.apply(parsec.connection,evt,parsec.cache)
                        except:
                            logging.getLogger("ORD_FAL").info("ORDER FAILED: Planet %s producing %s" % (planet, product_name))

        except:
            pass

        logging.getLogger("DONETRN").info("Finished ordering moves")
        return


def parse_ship((ship_id,num)):
    '''
    Map the output from pyke to the numbers wanted the server
    '''
    ship_tup = {}
    ship_name = {}
    ship_tup[0] = list(((1,num),))
    ship_name[0] = "Scouting"
    #FIXME HARDCODING OF 5
    ship_tup[1] = list(((3,num),))
    ship_name[1] = "Colonization"

    return ship_tup[ship_id], ship_name[ship_id]    

def parse_product(product_id):
    '''
    Map the output from pyke to the numbers wanted the server
    '''
    product_tup = {}
    product_name = {}
    product_tup[0] = ((7,1),)
    product_name[0] = "Colonists"

    return product_tup[product_id], product_name[product_id]

