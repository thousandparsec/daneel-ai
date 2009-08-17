import cPickle
import os
from time import gmtime, strftime, sleep
import sys
from tp.netlib.objects import OrderDescs

class ParsecGameStore(object):
    '''
    Object to store all the variables needed during the iteration of
    the gameloop.
    '''
    def __init__(self,rulesfile,engine,cache,connection,verbosity,learning=False,
                 saving=False, difficulty=0):
        self.rulesfile = rulesfile
        self.daneel_engine = engine
        self.cache = cache
        self.connection = connection
        self.verbosity = verbosity
        self.learning = learning
        self.saving = saving
        self.difficulty = difficulty
        try:
            self.weights = self.unpickle(os.path.join('rules', 'weights_' + self.rulesfile + "_" + self.difficulty.__str__() + '.dat'))
        except:
            # set all weights to one in case we couldn't load them
            self.weights = [1 for i in range(10)]
        self.pickled = False
        self.td = []
        

    def pickle(self, obj, filename):
        '''
        Wrapper for pickle.
        '''
        file = open(filename, 'wb')
        cPickle.dump(obj, file)
        file.close()
        return
    
    def unpickle(self,location):
        '''
        Wrapper for unpickle.
        '''
        file = open(location, 'rb')
        old_object = cPickle.load(file)
        file.close()
        return old_object

    def saveWeights(self):
        self.pickle(self.weights, os.path.join('rules', 'weights_' + self.rulesfile + "_" + self.difficulty.__str__() + '.dat'))

class Game(object):
    '''
    Interface common to all specific thousand parsec rulesets supported by daneel.
    '''
    def init(self,parsec):
        self.initKB(parsec)
        pass

    def startTurn(self, parsec,store_list=None):
        '''
        Parses the cache file. Inserts facts into the knowledge_base.
        '''
        
        # These are the attributes of each object in the cache we are going to store
        
        if store_list == None:
            store_list = ['subtype', 'name', 'owner', 'contains',
                           'resources', 'ships', 'damage', 'parent']
            
        for (id,player_object) in parsec.cache.players.iteritems():    
            parsec.daneel_engine.add_case_specific_fact('game', 'player', (id, player_object.name))  
              
        parsec.daneel_engine.add_case_specific_fact('game', 'whoami', (parsec.cache.players[0].id,))
        parsec.daneel_engine.add_case_specific_fact('game', 'turn', (parsec.cache.objects[0].turn,))

        self.parseCache(parsec,store_list, 'game', False)
        return


    def endTurn(self,parsec):
        '''
        Decision making process is undertaken in this function.
        '''
        pass
    
    
    def checkGame(self, parsec):
        '''
        Used to determine whether or not the game has finished.
        '''
        return 0


    def initKB(self, parsec):
        '''
        Inserts a single fact into each used knowledge_base.
        This is done to prevent a 
        '''
        parsec.daneel_engine.assert_('init', 'version', (.30,))
        parsec.daneel_engine.add_universal_fact('temp', 'nonempty', (True,))
        parsec.daneel_engine.add_universal_fact('game', 'nonempty', (True,))
        parsec.daneel_engine.add_universal_fact('orders', 'nonempty', (True,))
        return




    def parseCache(self, parsec, store_list=None, kb='init', activate=True):
        '''
        Iterates over cache.objects and stores the attribute in store_list
        of that object if it has it.
        if 
        '''

        # These are the default attributes of each object in the cache we are going to store
        # not used if a specific set of attributes is passed to the function.
        
        if store_list == None:
            store_list = ['subtype', 'owner', 'contains',
                           'resources', 
                           'ships', 'damage', 'start', 'end', 'size', 'pos', 'vel', 
                           'parent'
                           ]
            
        for (k,v) in parsec.cache.objects.iteritems():
            for attribute in store_list:
                if hasattr(v, attribute):
                    try:
                        sol = getattr(v, attribute)
                        try:
                            # conver lists to tuples because pyke wants to use tuples
                            if hasattr(sol, 'extend'):
                                sol = tuple(sol)
                        except:
                            pass
                        # we have found the attribute we want to store
                        parsec.daneel_engine.add_case_specific_fact(kb, attribute, (k, sol))
                    except:
                        pass
                else:
                    pass
        if activate:
            parsec.daneel_engine.activate( parsec.rulesfile )
        return