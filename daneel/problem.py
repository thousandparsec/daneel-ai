from constraint import *
import os
import sys
import daneel
import time


class DaneelProblem(Problem):
    
    
    def __init__(self, rulesfile, verbosity):
        Problem.__init__(self)
        self.verb = verbosity
        # Rules where the result can be carried over
        # each turn 
        self._constantRules = {}
        self._variableRules = {}
        self.mods = createRuleSystem(rulesfile)
         
   
    def addVariableRule(self, dict):
        for (k,v) in dict.items():
            if not (k in self._variableRules):
                self._variableRules[k] = v
            else:
                raise ValueError, "Tried to insert duplicated entry %s" % \
                                  repr(k)        
        return
    
    
    def getVariableRule(self, name):
        if not (name in self._variableRules):
            raise KeyError, "Value not found: %s" % \
                            repr(name)
        else:
            return self._variableRules[name]

    def getVariableRuleSolutions(self, name):
        if not (name in self._variableRules):
            raise KeyError, "Value not found: %s" % \
                            repr(name)
        else:
            return self._variableRules[name].getsol()
    
        
    def resetVaribles(self):
        self._variableRules = {}
        return
        
    def resetConstraints(self):
        del self._constraints[:]
        return
        
    def getConstantRules(self):
        return self._constantRules
    
    def getConstant(self, name):
        if not (name in self._constants):
            raise KeyError, "Value not found: %s" % \
                            repr(name)
        else:
            return self.constantRules[name]  
    
    def setConstant(self, name, domain):
        if name in self._constants:
            raise ValueError, "Tried to insert duplicated entry %s" % \
                              repr(name)
        if type(domain) in (list, tuple):
            domain = Domain(domain)
        elif isinstance(domain, Domain):
            domain = copy.copy(domain)
        else:
            raise TypeError, "Domains must be instances of subclasses of "\
                             "the Domain class"
        if not domain:
            raise ValueError, "Domain is empty"
        self._constants[name] = domain
        return
        
def createRuleSystem(rulesfile):
    mods = []
    rf = open(os.path.join(getDataDir(), 'rules', rulesfile))
    l = stripline(rf.readline())
    while l != "[Modules]":
        l = stripline(rf.readline())
    l = stripline(rf.readline())
    while l != "[Constraints]":
        if l != "":
            m = getattr(__import__("daneel."+l), l)
            mods.append(m)
        l = stripline(rf.readline())

    return mods

def getDataDir():
    
    if hasattr(sys, "frozen"):
        installpath = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
    else:
        installpath = os.path.realpath(os.path.dirname(__file__))
        
    if hasattr(sys, "frozen"):
        return os.path.join(installpath, "share", "daneel-ai")
    if "site-packages" in daneel.__file__:
        datadir = os.path.join(os.path.dirname(daneel.__file__), "..", "..", "..", "..", "share", "daneel-ai")
    else:
        datadir = os.path.join(os.path.dirname(daneel.__file__), "..")
    return datadir

def stripline(line):
    if line[0] == "#": return ""
    return line.strip()


def saveGame(cache,rulesfile,verbosity):
    root_dir = getDataDir()
    save_dir = os.path.join( root_dir, "states" )
    writeable = checkSaveFolderWriteable(root_dir, save_dir)
    # NB assumes there is enough space to write
    if not writeable:
        logging.getLogger("daneel").error("Cannot save information")
    else:       
        cache.file = os.path.join(save_dir, rulesfile + "_-_" + str(verbosity) + "_-_" + time.time().__str__() + ".gamestate")
        cache.save()


def checkSaveFolderWriteable(root_dir, save_dir):    
    dir_exists = os.access(save_dir, os.F_OK)
    dir_writeable = os.access(save_dir, os.W_OK)
    dir_root_writeable = os.access(root_dir, os.W_OK)
    if dir_exists and dir_writeable:
        return True
    if dir_exists and not dir_writeable:
        return False
    if dir_root_writeable:
        os.mkdir(save_dir)
        return True
    else:
        return False
    
    

class KnownRule(object):
    
    def __init__(self,name,domain):
        self._name = name
        self._solutions = domain
    def getsol(self):
        return self._solutions
    
    def getName(self):
        return self._name

        

class Rule(KnownRule):
    
    def __init__(self, store, name, vars,cons):   
        self._name = name
        self._variables = self.buildDicts(store,vars)
        self._constraints = cons
        self._solutions = None
        #TODO: Probably remove this
        self._type = None
        try:
            self.solve()
        except:
            pass
    
           
    def buildDicts(self,store,variables):
        dictlist = []
        for item in variables:
            if item['type'] == 'variable':
                try:
                    dictlist.append({'varname': item['varname'], 'value': store.getVariableRuleSolutions(item['varname'])})
                except:
                    pass
            else:
                try:
                    dictlist.append({'varname': item['varname'], 'value': store.getConstant(item['varname'])})
                except:
                    pass
        
        return dictlist


    def update(selfself,store,variables):
        self.buildDicts(store,variables)
        return
        
    def solve(self):
        return self._solve(self._variables, self._constraints)
        
    def _solve(self, varlist, cons):
        solvelist = []
        prob = Problem()
        
        for item in varlist:
             prob.addVariable('%s' % item['varname'], item['value'])
    
        for item in cons:
            if item['func'] and item['func_vars']:
                try:
                    prob.addConstraint(FunctionConstraint(item['func']), item['func_vars'])
                except:
                    pass
            # TODO: TEST THIS
            elif item['con']:           
                prob.addConstraint(item['con'], item['func_vars'])
    
        self._solutions = prob.getSolutions()
        return     
    

            