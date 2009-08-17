from daneel.common import Game as Cg
import daneel.common as common
import daneel.util as util
import logging
import tp.client.cache
import os
import sys

# these were the initial weights
#weights = [1,1,1.5,7,0]

class Game(Cg):

    def init(self, parsec):
        '''
        Called once at program startup.
        Initialises knowledge base facts that are always true.
        '''
        Cg.init(self,parsec)
        store_list = ['subtype','start', 'end','pos', 'parent']
        Cg.parseCache(self,parsec, store_list)
        self.setupAdjacentNodes(parsec)
        return

    def setupAdjacentNodes(self, parsec):
        '''
        Inserts all adjacent planets as a fact
        '''
        with parsec.daneel_engine.prove_n('parsec', 'adjacent', (), 2) as gen:
            for ((planet_one, planet_two), noplan) in gen:
                parsec.daneel_engine.add_universal_fact('init', 'adjacent', (planet_one, planet_two))
                parsec.daneel_engine.add_universal_fact('init', 'adjacent', (planet_two, planet_one))
        

        parsec.daneel_engine.reset('init')
        return


    def startTurn(self,parsec):
        # reset the kns
        parsec.daneel_engine.reset('game')
        parsec.daneel_engine.reset('orders')
        
        Cg.startTurn(self,parsec)
        parsec.daneel_engine.activate( parsec.rulesfile)
        return


    def proveWhoAmI(self, parsec):
        '''
        Tries to prove my_player_id
        '''
        with parsec.daneel_engine.prove_n('game', 'whoami', (), 1) as gen:
            for ((my_player_id,), noplan) in gen:
                pass
        return my_player_id

    def proveTurnNumber(self, parsec):
        '''
        Tries to prove the turn number
        '''
        with parsec.daneel_engine.prove_n('game', 'turn', (), 1) as gen:
            for ((turn,), noplan) in gen:
                pass
        return turn



    def endTurn(self,parsec):
        
        if parsec.learning == '1':
            my_player_id = self.proveWhoAmI(parsec)
            doScore(my_player_id, parsec, True)

        
        if parsec.saving == '1':
            logging.getLogger("daneel").info("Saving Cache")
            util.saveGame(parsec)
        
        my_player_id = self.proveWhoAmI(parsec)
        
        # predict what the enemy is likely to do
        predict(parsec, my_player_id)
        # make moves based on this fact
        
        doTurn(my_player_id, parsec)
        return



    def checkGame(self, parsec):
        '''
        Checks whether each player owns at least one planet. If not game is over.
        Aborts after 500 turns. (Game should have ended by then)"
        '''
        
        upper_limit = 500
        lower_limit = 2
        
        my_player_id = self.proveWhoAmI(parsec)
        turn = self.proveTurnNumber(parsec)
        
        
            
        if(turn > upper_limit):
            logging.getLogger("daneel").info("Game has gone on too long .. aborting")
            return -1

        if(turn < lower_limit):
            return 0
        
        
        planet_id = None
        #check that I own at least one planet
        with parsec.daneel_engine.prove_n('parsec', 'myplanet', (my_player_id,), 2) as gen:
            for ((planet_id,army_count), noplan) in gen:
                pass
        
        if(planet_id == None):
            logging.getLogger("daneel").info("I have no planets .. I loose")
            return -1

        enemy_planet_id = None
        #check that enemy owns at least one planet
        with parsec.daneel_engine.prove_n('parsec', 'player', (), 2) as gen:
            for ((player_id,name), noplan) in gen:
                if my_player_id == player_id:
                    pass
                else:
                    with parsec.daneel_engine.prove_n('parsec', 'myplanet', (player_id,), 2) as gen:
                        for ((enemy_planet_id,army_count), noplan) in gen:
                            pass
        
        
        if(enemy_planet_id == None):
            logging.getLogger("daneel").info("Enemy has no planets .. I win")
            return 1

        # continue playing
        return 0

def predict(parsec, my_id):
    '''
    Attempt to predict what other players are going to do so we 
    can act accordingly
    '''
    with parsec.daneel_engine.prove_n('parsec', 'player', (), 2) as gen:
        for ((player_id,name), noplan) in gen:
            if my_id == player_id:
                pass
            else:
                # set update to false so we don't try and send our opponents orders
                # to the server!
                doTurn(player_id, parsec, False)
    return

def doTurn(player_id, parsec, update=True):
    '''
    Carry out orders
    '''
    doReinforce(player_id, parsec, update)
    doExtraReinforceForAttack(player_id, parsec, update)
    doMove(player_id, parsec, update)
    return


def doScore(my_id, parsec, store_nodes=False):
    '''
    Returns the score of a player as a percentage in comparision with the strongest enemy
    
    '''
    enemymax = [-1000, None]
    with parsec.daneel_engine.prove_n('parsec', 'player', (), 2) as gen:
        for ((player_id,name), noplan) in gen:
            if my_id == player_id:
                my_score = playerScore(my_id, parsec)
            else:
                enemyscore = playerScore(player_id, parsec)
                if enemyscore[0] > enemymax[0]:
                    enemymax = enemyscore
                    
    if enemymax[0] == 0:
        enemymax[0] = 1
    
    finalscore = (my_score[0] / enemymax[0])
    
    # this section is called only if we are learning
    # store_nodes will only be true once a turn to update
    # the weights used in comparisons
    if store_nodes == True:
        finalnodes = []
        if enemymax[1] != None:
            i = 0
            for node in my_score[1]:
                finalnodes.append( node - enemymax[1][i] )
                i += 1
        
        parsec.td.append([finalscore, finalnodes])
        util.learn(parsec, 0)
        
    return finalscore


def playerScore(player_id, parsec, store_score = False):
    '''
    Calculates the score for a single player
    '''
    reinforcements = 0
    with parsec.daneel_engine.prove_n('parsec', 'reinforcements', (player_id,), 1) as gen:
        for ((reinforcements,), noplan) in gen:
            reinforcements = reinforcements

    planet_score = 0
    p_score = [0,0,0]
    with parsec.daneel_engine.prove_n('parsec', 'planet_score', (player_id,), 4) as gen:
        for ((planet_tup), noplan) in gen:
            # take the total of each node
            # troop_count, number of branches, safety factor
            p_score[0] += planet_tup[1]
            p_score[1] += planet_tup[2]
            p_score[2] += planet_tup[3]
#            print planet_tup[0], p_score
            
    p_score.append(reinforcements)
    
    
    # multilpy the sum of each node by its weight
    score, i = 0, 0
    for node in p_score:
        score += node * parsec.weights[i]
        i += 1
        
    return [score, p_score]


def doMove(player_id, parsec, update=True):
    move_dict = {}
    dest_dict = {}


    my_planets = []
    #  for each planet calculate the number of possible destinations and how
    # many each destination needs
    with parsec.daneel_engine.prove_n('parsec', 'myplanet', (player_id,), 2) as gen:
        for ((planet_id,army_count), noplan) in gen:
            my_planets.append(planet_id)
            used = 0
            with parsec.daneel_engine.prove_n('parsec', 'destinations', (player_id,planet_id,), 2) as gen:
                for ((destination,amount), available) in gen:
                    quota = available(used)
                    dest_dict[destination] = amount
                    try:
                        move_dict[planet_id]
                        move_dict[planet_id]['wanted'].append((destination, amount))
                    except:
                        move_dict[planet_id] = {'quota': quota, 'wanted':[(destination, amount)]}

    # Set so high not to conflict with any armies already in the kb which
    # were added via the reinforce rules
    i = 2000 
    init_score = doScore(player_id,parsec)
    for (k,v) in move_dict.iteritems():
        ll = []
        # this is used to represent the do nothing move
        ll.append((-1,-1,v['quota'], 0))
        used = 0
        for (destination,amount) in v['wanted']:
            av = min(v['quota'], amount)
            parsec.daneel_engine.assert_('temp', 'armies', (player_id, i, destination, av))
            parsec.daneel_engine.assert_('temp', 'armies', (player_id, i, k, -1 * av))
            i += 1
            used += av
            score = doScore(player_id,parsec)
            ll.append((k, destination, av, score - init_score))
            parsec.daneel_engine.reset('temp')
            parsec.daneel_engine.activate('risk')
            
        choice_tuple = tuple(ll)
        qmax = -1
        best_ans = None
        
        # calculate the best combination
        with parsec.daneel_engine.prove_n('parsec', 'best_combo', (choice_tuple, v['quota']), 1) \
          as gen:
            for (combination,), no_plan in gen:
                score = sum(map(lambda x: x[3], combination))
                if score > qmax:
                    qmax = score
                    best_ans = combination
            
            if best_ans == ():
                llb = None
            else:
                llb = best_ans
                
        v_used = 0
        
        
        if llb:                    
            for (source, destination, amount, score) in llb:
                if source > 0:
                    i += 1
                    # move the armies in the kb
                    parsec.daneel_engine.assert_('orders', 'armies', (player_id, i, destination, amount))
                    parsec.daneel_engine.assert_('orders', 'armies', (player_id, i, source, -1 * amount))
                    v_used += amount
                    if update:
                        createMoveOrder((source, destination, amount), 'Move', parsec, True)
                else:
                    pass # DOING NOTHING
                
        # Here we try and 'hang on' as described in the risk screen cast to improve our odds when
        # we are likely to be attacked.
        if v_used < v['quota']:
            for node in choice_tuple:
                if v_used > v['quota']:
                    pass
                if node[0] == -1:
                    pass
                elif node not in llb:
                    if node[1] not in my_planets:
                        i += 1
                        parsec.daneel_engine.assert_('orders', 'armies', (player_id, i, node[1], 1))
                        v_used += amount
                        if update:
                            #print "HANGING ON"
                            createMoveOrder((node[0], node[1], 1), 'Move', parsec, True)
                    else:
                        pass
                    
    return

def doReinforce(player_id, parsec, update=True):
    reinforcements = 0
    
    with parsec.daneel_engine.prove_n('parsec', 'reinforcements', (player_id,), 1) as gen:
        for ((reinforcements,), noplan) in gen:
            pass
        

    # while we have reinforcements we try and distribute them to satisfy each of our planets needs
    
    if reinforcements > 0:
        remaining = reinforcements
        i = 0
        while(remaining > 0):
            i += 1
            reinforcements = max(1, (remaining + 1 )/2)
            curr_max_list = []
            currmax = (-500, None)
            curr_max_list.append(currmax)
            with parsec.daneel_engine.prove_n('parsec', 'myplanet', (player_id,), 2) as gen:
                for ((planet_id, army_num), noplan) in gen:
                    # get the minimum amount of armies each planet needs
                    with parsec.daneel_engine.prove_n('parsec', 'minimum', (0,player_id,planet_id,), 1) as gen:
                        for (((required,)), noplan) in gen:
                            # check whether we have enough
                            if required <= army_num:
                                pass
                            else:
                                # needs armies.. see if it is worth doing
                                parsec.daneel_engine.assert_('temp', 'armies', (player_id, i, planet_id, min(required - army_num, reinforcements)))
                                score = doScore(player_id,parsec)
                                if score > currmax[0]:
                                    currmax = (score, (planet_id, min(required - army_num, reinforcements)))
                                    
                                curr_max_list.append((score, (planet_id, min(required - army_num, reinforcements))))
                                parsec.daneel_engine.reset('temp')
                                parsec.daneel_engine.activate('risk')
                                
            # do the best move we have found
            if currmax[1]:
                if update:                
                    createReinforceOrder((currmax[1][0], currmax[1][1]), 'Reinforce', parsec, True)
                else:
                    #print "PREDICTING REINFORCE"
                    pass
                parsec.daneel_engine.assert_('orders', 'armies', (player_id, i, currmax[1][0], currmax[1][1]))
                #reduce the number of available reinforcements
                remaining -= currmax[1][1]
            else:
                remaining = 0
                 
                
                
    else:
        pass
    
    return
            


def doExtraReinforceForAttack(player_id, parsec, update=True):
    '''
    If we still have any available reinforcements after making sure we are defended adequately
    .. consider adding more to facilitate an attack move
    '''
    reinforcements = 0
    with parsec.daneel_engine.prove_n('parsec', 'reinforcements', (player_id,), 1) as gen:
        for ((reinforcements,), noplan) in gen:
            pass
        
    
    if reinforcements > 0:
        remaining = reinforcements
        # set so high not conflict with other functions when they assert temp,armies
        i = 1000 
        while(remaining > 0):
            i += 1
            reinforcements = max(1, (remaining + 1 )/2)
            currmax = (doScore(player_id,parsec), None)
            with parsec.daneel_engine.prove_n('parsec', 'adjacentenemies', (player_id,), 4) as gen:
                for ((planet_id, army_num, enemy_planet_id, enemy_army_num), noplan) in gen:
                    # attacking is not recommended .. only do so if we greatly outnumber the opponent
                    required = round(3 * enemy_army_num + 1)
                        
                    if required <= army_num:
                        pass
                    else:
                        parsec.daneel_engine.assert_('temp', 'armies', (player_id, i, planet_id, min(required - army_num, reinforcements)))
                        score = doScore(player_id,parsec)
                        if score > currmax[0]:
                            currmax = (score, (planet_id, min(required - army_num, reinforcements)))
                        parsec.daneel_engine.reset('temp')
                        parsec.daneel_engine.activate('risk')
                # do the best order                
                if currmax[1]:
                    if update:                
                        createReinforceOrder((currmax[1][0], currmax[1][1]), 'Reinforce', parsec, True)
                    else:
                        #print "PREDICTING REINFORCE"
                        pass
                    parsec.daneel_engine.assert_('orders', 'armies', (player_id, i, currmax[1][0], currmax[1][1]))
                    # reudce the amount available
                    remaining -= currmax[1][1]
                else:
                    remaining = 0
                 
                
                
    else:
        pass
    
    return




def createReinforceOrder(params, order_type, parsec, update=True):
    '''
    Triggers a reinforcement order into the cache
    '''
    if parsec.pickled == False:
        order = util.findOrderDesc(order_type)
        args = [0, params[0], -1, order.subtype, 0, [], int(params[1]), 0]
        makeorder = order(*args)
        try:
            if update != False:
                evt = parsec.cache.apply("orders","create after",params[0],parsec.cache.orders[params[0]].last,makeorder)
                tp.client.cache.apply(parsec.connection,evt,parsec.cache)
            logging.getLogger("ORD_REF").info("Reinforcing %s with %s troops" % (params[0], int(params[1])))
        except:
            pass
    else:
        logging.getLogger("ORD_REF").info("Reinforcing %s with %s troops" % (params[0], int(params[1])))



def createMoveOrder(params, order_type, parsec, update=True):

    '''
    Triggers a move order into the cache. If the amount of troops
    is greater than three we chain the move.
    '''
    
    total = int(params[2])
    while(total > 0):
        if total > 3:
            chain_amount = min(3,total)
        else:
            chain_amount = total
        total -= chain_amount
        if parsec.pickled == False:
            order = util.findOrderDesc(order_type)
            args = [0, params[0], -1, order.subtype, 0, [], ([], [(params[1], chain_amount)])]
            makeorder = order(*args)
            try:
                if update != False:
                    evt = parsec.cache.apply("orders","create after",params[0],parsec.cache.orders[params[0]].last,makeorder)
                    tp.client.cache.apply(parsec.connection,evt,parsec.cache)
                logging.getLogger("ORD_MVE").info("Moving %s troops from %s to %s" % (chain_amount, params[0], params[1]))
            except:
                logging.getLogger("ORD_FAL").info("ORDER FAILED: Moving %s troops from %s to %s" % ( chain_amount, params[0], params[1]))
        else:
            logging.getLogger("ORD_MVE").info("Moving %s troops from %s to %s" % (chain_amount, params[0], params[1]))
