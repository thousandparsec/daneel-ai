from functools import partial

import re

class RuleSystem:
    def __init__(self,constraints=[],rules=[],functions={}):
        self.constraints = constraints
        self.store = ConstraintStore()
        self.activestore = ConstraintStore()
        self.parser = RuleParser(constraints)
        self.rules = [self.parser.parseRule(r) for r in rules]
        self.basecontext = self.createBaseContext(functions)

    def addConstraint(self,constraint):
        parsedcon = self.parser.parseConstraint(constraint)
        self.store.add(parsedcon)
        self.activestore.add(parsedcon)
        while len(self.activestore) > 0:
            activecon = self.activestore.pop()
            self.matchActive(activecon)

    def removeConstraint(self,constraint):
        try:
            self.activestore.remove(constraint)
        except KeyError:
            pass
        self.store.remove(constraint)

    def matchActive(self,constraint):
        for r in self.rules:
            if r.matchActive(constraint):
                break

    def clearStore(self):
        #TODO: long-term storage
        self.store.clear()
        self.activestore.clear()

    def createContext(self):
        return self.basecontext.copy()

    def createBaseContext(self,functions):
        context = functions.copy()
        #we insert a function for each constraint. When this function is called,
        #a new instance of the constraint gets inserted in the constraint store
        #with arguments as passed with the function
        def createCons(name,*args):
            cons = BoundConstraint(name,list(args))
            self.addConstraint(cons)
        for c in self.constraints:
            context[c] = partial(createCons,c)
        return context

    def findConstraint(self,con):
        return [x for [x] in self.findConstraints([self.parser.parseConstraint(con)])]

    def findConstraints(self,cons,excluded=set()):
        return self.store.findterms(cons,excluded)

class RuleParser:
    uniquecount = 0
    freecon = re.compile(r"^(\w*)/(\d*)$")
    boundcon = re.compile(r"^(\w+)(\( *(.+?, *)*.+ *\))?$")

    def __init__(self,constraints=[]):
        self.constraints = constraints

    def parseRule(self,rule):
        if isinstance(rule,Rule):
            return rule

    def parseConstraint(self,cons):
        if isinstance(cons,Constraint):
            return cons
        m = RuleParser.freecon.match(cons)
        if m is not None:
            return FreeConstraint(m.group(1),int(m.group(2)))
        m = RuleParser.boundcon.match(cons)
        if(m is not None):
            functor = m.group(1)
            args = []
            if(m.group(2) is not None):
                args = m.group(2)[1:-1].split(",")
            return BoundConstraint(functor,args)

class Rule:
    """A rule consist of:
    * name, string, preferable unique although nothing requires this
    * kepthead, list of free constraints
    * removedhead, list of free constraints
    * guard, Python code evaluating to True or False represented as string
    * body, a mix of constraints, PythonTerms and unifications, represented as string"""

    def __init__(self,rulesystem):
        self.rulesystem = rulesystem
        self.name = "!notinitialized!"
        self.kepthead = []
        self.removedhead = []
        self.guard = "True"
        self.body = ""

    def matchActive(self,con):
        positions = self.canAcceptAt(con)
        if(positions == []):
            return False
        allConstraints = self.kepthead + self.removedhead
        for pos in positions:
            neededConstraints = [allConstraints[i] for i in range(len(allConstraints)) if i!=pos]
            partners = self.rulesystem.findConstraints(neededConstraints,set([con]))
            for p in partners:
                    p.insert(pos,con)
            for p in partners:
                assert len(p) == len(self.kepthead) + len(self.removedhead)
                context = self.rulesystem.createContext()

                #bind vars
                for i in range(len(p)):
                    tempcon = p[i]
                    for j in range(tempcon.arity):
                        var = "_var_%i_%i" % (i,j)
                        context[var] = tempcon.args[j]

                if eval(self.guard,context):
                    #print "Rule fired: %s" % self.name
                    if self.removedhead == []:
                        removedConstraints = []
                    else:
                        removedConstraints = p[-len(self.removedhead):]
                    for c in removedConstraints:
                        self.rulesystem.removeConstraint(c)
                    exec(self.body,context)
                    return True

    def canAcceptAt(self,cons):
        head = self.kepthead + self.removedhead
        return [i for i in range(len(head)) if head[i].unifiesWith(cons)]

class ConstraintStore:
    """A CHR constraint store is used to hold a collection of facts in the form of predicates."""
    def __init__(self):
        self.elems = {}

    def add(self,elem):
        assert isinstance(elem,Constraint), "%s is not a Constraint" % (elem, )
        func = elem.functor
        ar = elem.arity
        if(self.elems.has_key((func,ar))):
            self.elems[(func,ar)].add(elem)
        else:
            self.elems[(func,ar)] = set([elem])

    def remove(self,elem):
        assert isinstance(elem,Constraint), "%s is not a Constraint" % (elem, )
        func = elem.functor
        ar = elem.arity
        self.elems[(func,ar)].remove(elem)

    def __len__(self):
        return sum(map(len,self.elems.values()))

    def __str__(self):
        return str(self.elems.values())

    def findterms(self,terms,previousterms=set()):
        """Matches a list of strings against the store. Returns a list of predicate lists that match.
        Variables will not be bound yet as these are tentative choices.
        Note that all arguments should be unbounded and different (head-normal form of rules).
        For example: match(["pred(X)","pred2(Y,Z)"]) might return [[pred(5),pred2(5,7)],[pred(""),pred2("x",3)]]"""
        #TODO: this might become a generator to avoid having to calculate all answers (list of combinatorial size)
        if terms == []:
            return [[]]
        terms.reverse()
        return self.findmatches(terms,previousterms)

    def findmatches(self,needles,previousterms):
        newneedles = list(needles)
        constr = newneedles.pop()
        if(isinstance(constr,Constraint)):
            possiblematches = self.elems[constr.functor,constr.arity].difference(previousterms)
            if newneedles == []:
                return [[x] for x in possiblematches]
            finallist = []
            for x in possiblematches:
                usedterms = set(previousterms)
                usedterms.add(x)
                for y in self.findmatches(newneedles,usedterms):
                    finallist.append([x] + y)
            return finallist
        else:
            assert False #TODO: PythonTerm?

    def pop(self):
        v = self.elems.values()
        for s in v:
            if len(s) > 0:
                return s.pop()

    def clear(self):
        self.elems.clear()

class Constraint:
    def __init__(self,name,arity):
        self.functor = name
        self.arity = arity

class FreeConstraint(Constraint):
    """A constraint with all arguments unbounded (different variables)."""
    def __init__(self,name,arity):
        Constraint.__init__(self,name,arity)

    def __str__(self):
        return "%s/%i" % (self.functor,self.arity)

    def __repr__(self):
        return "<FreeConstraint: %s at 0x%x>" % (str(self),id(self))

    def bind(self,args):
        assert len(args) == self.arity
        return BoundConstraint(self.name,args)

    def unifiesWith(self,other):
        return self.functor == other.functor and self.arity == other.arity

class BoundConstraint(Constraint):
    """A constraint with all arguments known Python expressions."""
    def __init__(self,name,args):
        Constraint.__init__(self,name,len(args))
        self.args = args

    def __str__(self):
        if(self.args == []):
            return self.functor
        else:
            return "%s(%s)" % (self.functor, ','.join([str(x) for x in self.args]))

    def __repr__(self):
        return "<BoundConstraint: %s at 0x%x>" % (str(self),id(self))

    def unifiesWith(self,other):
        if(hasattr(other,"args")):
            return self.functor == other.functor and self.arity == other.arity and self.args == other.args
        else:
            return other.unifiesWith(self)
