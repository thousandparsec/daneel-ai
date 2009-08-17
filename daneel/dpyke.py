from pyke import knowledge_engine

class engine( knowledge_engine.engine):
    '''
    A class to extend the pyke knowledge_engine
    with a modified reset function, to allow for
    the resetting of a single knowledge_base at a time.
    '''
    def reset(self, resetted=None):
        '''
        Modified version of the reset function found in
        pyke.knowledge_engine. Reset all the rule bases.
        Just reset a single knowledge_base 'resetted' .. or all knowledge_bases
        '''
        for rb in self.rule_bases.itervalues():
            rb.reset()
        for kb in self.knowledge_bases.itervalues():
            if resetted:
                if kb.name == resetted:
                    kb.reset()
                else:
                    pass
            else:
                kb.reset()
                
                
                
def repairPickle(engine):
    '''
    Function to repair the knowledge_engine object when it is unpickled.
    Workaround to fix a current bug in pyke 1.02 when pickling / unpickling
    a knowledge_engine object.
    '''
    for (k,v) in engine.rule_bases.iteritems():
        v.engine = engine
        