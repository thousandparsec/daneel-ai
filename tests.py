import daneel.util as util
import daneel.common as common
import daneel.dpyke as fixpyke
from daneel_ai import *
import os
import unittest
import time



class TestDaneelFunctions(unittest.TestCase):

    def setUp(self):
        pickled = common.ParsecGameStore(None,None,None,None,None)
        pickled = pickled.unpickle(os.path.join('states', 'data.dat'))
        fixpyke.repairPickle(pickled.daneel_engine)

        self.parsec = pickled

    def testprove(self):
        my_player_id = None
        with self.parsec.daneel_engine.prove_n('game', 'whoami', (), 1) as gen:
            for ((my_player_id,), noplan) in gen:
                pass

        self.assert_(my_player_id != None)


    def testreset(self):

        self.parsec.daneel_engine.reset('init')
        my_player_id = None
        with self.parsec.daneel_engine.prove_n('game', 'whoami', (), 1) as gen:
            for ((my_player_id,), noplan) in gen:
                pass

        self.assert_(my_player_id != None)


    def testreset2(self):

        self.parsec.daneel_engine.reset('game')
        my_player_id = None
        with self.parsec.daneel_engine.prove_n('game', 'whoami', (), 1) as gen:
            for ((my_player_id,), noplan) in gen:
                pass

        self.assert_(my_player_id == None)


    def testlearn(self):


        old_weights = self.parsec.weights
        util.learn(self.parsec)
        
        self.assert_(old_weights != self.parsec.weights)




if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDaneelFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)

