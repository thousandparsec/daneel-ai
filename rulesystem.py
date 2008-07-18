from functools import partial
from collections import defaultdict

from logilab.constraint import fd, Solver, Repository
from logilab.constraint.fd import ConsistencyFailure

import re

def totype(v,t):
    if type(v) == str:
        if t == str and not (v[0] in "'\"" and v[0] == v[-1]):
            return t(v)
        else:
            return t(eval(v))
    elif isinstance(v,t):
        return v
    else:
        return t(v)

class RuleSystem:
    def __init__(self,constraints=[],rules=[],functions={}):
        self.parser = RuleParser(self)
        cons = [self.parser.parseFreeConstraint(x) for x in constraints]
        self.bcfactory = BoundConstraintFactory(cons)
        self.constraints = self.bcfactory.constraints
        self.store = ConstraintStore()
        self.activestore = ConstraintStore()
        self.rules = [self.parser.parseRule(r) for r in rules]
        self.protocontext = self.createPrototypeContext(functions)

    def addConstraint(self,constraint):
        #print "Adding constraint %s" % constraint
        parsedcon = self.parser.parseBoundConstraint(constraint)
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

    def hasConstraints(self,cons):
        for con in cons:
            if not self.store.hasConstraint(con): return False
        return True

    def matchActive(self,constraint):
        for r in self.rules:
            if r.matchActive(constraint):
                break

    def clearStore(self):
        self.store.clear()
        self.activestore.fullclear()
        for r in self.rules:
            r.history = set()

    def createContext(self):
        return self.protocontext.copy()

    def createPrototypeContext(self,functions):
        context = functions.copy()
        #we insert a function for each constraint. When this function is called,
        #a new instance of the constraint gets inserted in the constraint store
        #with arguments as passed with the function
        def createCons(name,*args):
            cons = self.bcfactory.createConstraint(name,list(args))
            self.addConstraint(cons)
        for c in self.constraints:
            context[c] = partial(createCons,c)
        return context

    def findConstraint(self,con):
        """Given a free constraint, returns a list of constraints in the store that match it"""
        con = self.parser.parseFreeConstraint(con)
        return list(self.store.elems[(con.functor,con.arity)])

class RuleParser:
    con = re.compile(r"^(\w+)(\( *(.+?, *)*.+ *\))?(\*)?$")
    #these regexps might be a bit too loose, then again, we're trying to match a CFL.
    #probably, it can be compiled in one RE too.
    simplrule = re.compile(r"^((?P<name>\w+) @ )?(?P<removedhead>[^\\]+)<=>((?P<guard>.+)\|)?(?P<body>.+)$")
    simparule = re.compile(r"^((?P<name>\w+) @ )?(?P<kepthead>.+)\\(?P<removedhead>.+)<=>((?P<guard>.+)\|)?(?P<body>.+)$")
    proprule = re.compile(r"^((?P<name>\w+) @ )?(?P<kepthead>.+)==>((?P<guard>.+)\|)?(?P<body>.+)$")

    uniquecount = 0

    def __init__(self,rulesystem):
        self.rulesystem = rulesystem

    def parseRule(self,rule):
        if isinstance(rule,Rule):
            return rule
        return self.tryRuleMatch(rule,RuleParser.simplrule) or\
                self.tryRuleMatch(rule,RuleParser.simparule) or\
                self.tryRuleMatch(rule,RuleParser.proprule)

    def parseFullRule(self,name=None,kepthead=[],removedhead=[],guard=[],body=""):
        RuleParser.uniquecount = RuleParser.uniquecount + 1
        if name is None:
            name = "rule_%i" % RuleParser.uniquecount
        rule = Rule(self.rulesystem)
        rule.name = name
        self.parseHead(kepthead,removedhead,rule)
        rule.guard.extend(self.parseGuard(guard,rule))
        rule.body = self.parseBody(body)
        return rule

    def tryRuleMatch(self,rule,pattern):
        m = pattern.match(rule)
        if m is not None:
            d = dict([(i,m.groupdict()[i]) for i in m.groupdict() if m.groupdict()[i] is not None])
            return self.parseFullRule(**d)

    def parseHead(self,kepthead,removedhead,rule):
        kepthead = self.splitHead(kepthead)
        rule.kepthead = [self.rulesystem.bcfactory.getFreeConstraint(func,args) for (func,args) in kepthead]
        removedhead = self.splitHead(removedhead)
        rule.removedhead = [self.rulesystem.bcfactory.getFreeConstraint(func,args) for (func,args) in removedhead]
        head = kepthead + removedhead
        for (i,(functor,args)) in enumerate(head):
            types = self.rulesystem.bcfactory.getFreeConstraint(func,args).types
            for (j,arg) in enumerate(args):
                if arg[0].isupper():
                    if not arg in rule.extravars:
                        rule.extravars.append(arg)
                    rule.guard.append(fd.make_expression(("_var_%i_%i"%(i,j),arg),"_var_%i_%i == %s"%(i,j,arg)))
                else:
                    rule.guard.append(fd.Equals("_var_%i_%i"%(i,j),totype(arg,types[j])))

    def splitHead(self,head):
        if isinstance(head,list):
            return head
        splitted = head.split(" and ")
        return [self.parseConstraint(x.strip()) for x in splitted]

    def parseGuard(self,guard,rule):
        if isinstance(guard,list):
            return guard
        parts = guard.split(" and ")
        return [fd.make_expression(rule.extravars,g) for g in parts]

    def parseBody(self,body):
        return body.strip()

    def parseFreeConstraint(self,cons):
        if isinstance(cons,FreeConstraint):
            return cons
        m = RuleParser.con.match(cons)
        assert m is not None
        functor = m.group(1)
        types = []
        if(m.group(2) is not None):
            types = m.group(2)[1:-1].split(",")
        longterm = m.group(4) == "*"
        return FreeConstraint(functor,map(eval,types),longterm)

    def parseConstraint(self,cons):
        m = RuleParser.con.match(cons)
        assert m is not None
        functor = m.group(1)
        args = []
        if(m.group(2) is not None):
            stack = []
            i = m.group(2)[1:-1]
            args = []
            word = ""
            matchesstart = "([\"'"
            matchesstop = ")]\"'"
            for c in i:
                if c in matchesstop and len(stack) > 0:
                    p = matchesstart.index(stack[-1])
                    if(matchesstop[p] == c):
                        stack.pop()
                    else: #either wrong, or " or '
                        stack.append(c)
                    word = word + c
                elif c in matchesstart:
                    stack.append(c)
                    word = word + c
                elif c == "," and stack == []:
                    args.append(word)
                    word = ""
                else:
                    word = word + c
            args.append(word.strip())
        return (functor,args)

    def parseBoundConstraint(self,con):
        if isinstance(con,Constraint):
            return con
        (functor,args) = self.parseConstraint(con)
        return self.rulesystem.bcfactory.createConstraint(functor,args)

class Rule:
    """A rule consist of:
    * name, string, preferable unique although nothing requires this
    * kepthead, list of free constraints
    * removedhead, list of free constraints
    * guard, List of Python code evaluating to True or False represented as string
    * body, a mix of constraints, PythonTerms and unifications, represented as string"""

    def __init__(self,rulesystem):
        self.rulesystem = rulesystem
        self.name = None
        self.kepthead = []
        self.removedhead = []
        self.extravars = []
        self.guard = []
        self.body = ""
        self.history = set()

    def matchActive(self,con):
        """Tries to match a given constraint against this rule.
        Returns True if the constraint is removed from the store in the process."""
        positions = self.canAcceptAt(con)
        if(positions == []):
            return False
        for pos in positions:
            if self.matchAtPosition(con,pos):
                return pos >= len(self.kepthead)
        return False

    def matchAtPosition(self,con,pos):
        allConstraints = self.kepthead + self.removedhead
        var1 = ["_var_%i" % i for i in range(len(allConstraints))]
        var2 = ["_var_%i_%i" % (i,j) for i in range(len(allConstraints)) for j in range(allConstraints[i].arity)]

        domains = {}
        allvals = []
        for i in range(len(allConstraints)):
            c = "_var_%i" % i
            vals = self.rulesystem.findConstraint(allConstraints[i])
            if vals == []:
                return False
            domains[c] = fd.FiniteDomain(vals)
            for j in range(allConstraints[i].arity):
                c2 = "%s_%i" % (c,j)
                vals2 = [x.args[j] for x in vals]
                domains[c2] = fd.FiniteDomain(vals2)
                allvals.extend(vals2)
        for i in self.extravars:
            domains[i] = fd.FiniteDomain(allvals)

        variables = var1 + var2 + self.extravars

        constraints = []
        if(len(var1) > 1):
            constraints.append(fd.AllDistinct(var1))
        constraints.append(fd.Equals("_var_%i" % pos,con))
        for i in range(len(allConstraints)):
            for j in range(allConstraints[i].arity):
                c = "_var_%i" % i
                a = "_var_%i_%i" % (i,j)
                constraints.append(fd.make_expression((c,a),"%s.args[%i] == %s"%(c,j,a)))
        constraints.extend(self.guard)

        try:
            #print "vars " + str(variables)
            #print "domains " + str(domains)
            #print "cons " + str(constraints)
            #print ""
            r = Repository(variables, domains, constraints)
            solutions = Solver().solve(r, False)
        except ConsistencyFailure:
            return False
        if solutions is None:
            return False
        for solution in solutions:
            p = [solution["_var_%i"%i] for i in range(len(allConstraints))]
            assert len(p) == len(self.kepthead) + len(self.removedhead)
            if tuple(p) in self.history: continue
            if self.rulesystem.hasConstraints(p):
                context = self.rulesystem.createContext()

                #bind vars
                for i in range(len(p)):
                    tempcon = p[i]
                    for j in range(tempcon.arity):
                        var = "_var_%i_%i" % (i,j)
                        context[var] = tempcon.args[j]
                for v in self.extravars:
                    context[v] = solution[v]
                #print "Rule fired: %s" % self.name
                if self.removedhead == []:
                    removedConstraints = []
                else:
                    removedConstraints = p[-len(self.removedhead):]
                for c in removedConstraints:
                    self.rulesystem.removeConstraint(c)
                self.history.add(tuple(p))
                exec(self.body,context)

    def canAcceptAt(self,cons):
        head = self.kepthead + self.removedhead
        return [i for i in range(len(head)) if head[i].unifiesWith(cons)]

class ConstraintStore:
    """A CHR constraint store is used to hold a collection of facts in the form of predicates."""
    def __init__(self):
        self.elems = defaultdict(set)

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

    def hasConstraint(self,elem):
        assert isinstance(elem,Constraint), "%s is not a Constraint" % (elem, )
        func = elem.functor
        ar = elem.arity
        return elem in self.elems[(func,ar)]

    def __len__(self):
        return sum(map(len,self.elems.values()))

    def __str__(self):
        return str(self.elems.values())

    def pop(self):
        v = self.elems.values()
        for s in v:
            if len(s) > 0:
                return s.pop()

    def clear(self):
        for (k,v) in self.elems.items():
            if v != set():
                el = v.pop()
                if el.freecon.longterm:
                    v.add(el)
                else:
                    self.elems[k] = set()

    def fullclear(self):
        self.elems.clear()

class Constraint:
    def __init__(self,name,arity):
        self.functor = name
        self.arity = arity

class FreeConstraint(Constraint):
    """A constraint with all arguments unbounded (different variables)."""
    def __init__(self,name,types,longterm=False):
        Constraint.__init__(self,name,len(types))
        self.types = types
        self.longterm = longterm

    def __str__(self):
        return "%s(%s)" % (self.functor, ','.join([str(x) for x in self.types]))

    def __repr__(self):
        return "<FreeConstraint: %s at 0x%x>" % (str(self),id(self))

    def bind(self,args):
        assert len(args) == self.arity
        return BoundConstraint(self.name,args)

    def unifiesWith(self,other):
        if self.functor != other.functor or self.arity != other.arity:
            return False
        for (i,t) in enumerate(self.types):
            if not isinstance(other.args[i],t):
                return False
        return True

class BoundConstraint(Constraint):
    """A constraint with all arguments known Python expressions."""
    def __init__(self,name,args,freecon):
        Constraint.__init__(self,name,len(args))
        self.args = args
        self.freecon = freecon

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

class BoundConstraintFactory:
    def __init__(self,cons=[]):
        self.constraints = dict(zip([x.functor for x in cons],cons))

    def createConstraint(self,name,args):
        basiccon = self.constraints[name]
        assert len(args) == len(basiccon.types)
        for (i,t) in enumerate(basiccon.types):
            args[i] = totype(args[i],t)
        return BoundConstraint(name,args,basiccon)

    def getFreeConstraint(self,functor,args):
        if not isinstance(args,int):
            args = len(args)
        return self.constraints[functor]