import cProfile
import pstats
import daneel_ai
import os
import logging
import sys
import StringIO
import re
import picklegamestate
import cPickle
from daneel_ai import gameLoopBenchMark
from tp.client.cache import Cache

state_dir = "./states/"

	
def isGameStateFile(file_name):
	return re.search('.*gamestate$', file_name)
	

def unpickle(pickle_location):
	file = open(pickle_location, 'rb')
	old = cPickle.load(file)
	file.close()
	return old
	
	
def getPickledStates():
	global state_dir
	file_list = os.listdir(state_dir)
	return filter(isGameStateFile, file_list)



class FakeStdOut(object):
	# wrapping class that
	# means we can pipe stdout to a file and stdout if we want
	def __init__(self, filename, mode):
		self.file = open(filename, mode)
		self.stderr = sys.stderr
		sys.stderr = self
		
	def __del__(self):
		self.close()
		
	def close(self):	
		if self.stderr  is not None:
			sys.stderr = self.stderr
			self.stderr = None
		if self.file is not None:
			self.file.close()
			self.file = None
	
	def write(self, data):
		self.file.write(data)	
	#	self.stderr.write(data)
	
	

if __name__=='__main__':
	global state_dir
	list_of_states = getPickledStates()

	turns = 0
	connection = None
	
	for state in list_of_states:
		basename = state.partition('.')
		output = state_dir + basename[0]  + ".out"
		profile = state_dir + state  + ".profile"
		
		try:
			cache = Cache('dummy_val')
			cache.file = state_dir + state
			cache.load()
	
			filesplit = re.split('\_-_+', state)	
			rulesfile = filesplit[0]
			verbosity = int(filesplit[1])
	
			cProfile.runctx('gameLoopBenchMark(rulesfile,turns,connection,cache,verbosity)', globals(), locals(), profile)	
			
			file = FakeStdOut(output, 'w')
			p = pstats.Stats(profile,stream=file)
			
			p.strip_dirs().sort_stats('time').print_stats(100)
			file.close()
			
		except:
			pass
			

		
	

		
	
