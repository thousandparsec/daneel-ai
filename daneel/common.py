class Game(object):

    def init(self,cache,daneel_engine,connection):
        pass

    def startTurn(self,cache,daneel_engine,store_list=None, delta=0):
        player, whoami,turn,objects = [], [], [], []
        
        if store_list == None:
            store_list = ['subtype', 'name', 'size', 'pos', 'vel', 'owner', 'contains',
                           'resources', 'ships', 'damage', 'start', 'end'
                           ]

            
        last_time = getLastTurnTime(cache,delta)       
        for (k,v) in cache.players.items():    
            daneel_engine.add_case_specific_fact('game', 'player', (k, v.name))  
            player.append ( (k, v.name) )
              
        whoami.append (cache.players[0].id)
        turn.append(cache.objects[0].turn)
        daneel_engine.add_case_specific_fact('game', 'whoami', (cache.players[0].id,))
        daneel_engine.add_case_specific_fact('game', 'turn', (cache.objects[0].turn,))
        

            
        for (k,v) in cache.objects.items():
            element = {}
            if delta and cache.objects.times[k] < last_time:
                pass
            else:
                    element['id'] = k
                    element['time_modified'] = cache.objects.times[k]
                    for attribute in store_list:
                        if hasattr(v, attribute):
                            try:
                                sol = getattr(v, attribute)
                                try:
                                    if hasattr(sol, 'extend'):
                                        sol = tuple(sol)
                                except:
                                    pass
                                element[attribute] = sol
                                daneel_engine.add_case_specific_fact('game', attribute, (k, sol))
                            except:
                                pass
                            if attribute == 'resources':
                                try:
                                    #logging.getLogger('RESOURCES').debug( getattr(v, attribute)[0][1] )
                                    pass
                                except:
                                    pass
                        else:
                            pass
                            
            objects.append( element)
        
        dict_of_lists = {'player': player, 'whoami': whoami, 'turn': turn, 'objects': objects}
        #daneel_engine.get_kb('game').dump_specific_facts()
        # store.addVariableRule(dict_of_lists)
        return


    def endTurn(self,cache,daneel_engine,connection):
        pass


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
