import csv
from sklearn import tree
import numpy as np
from sklearn.tree import DecisionTreeClassifier
import sys, os, inspect
from jmoo_objective import *
from jmoo_decision import *
from jmoo_problem import jmoo_problem
import pdb

def avg(lst):
    return sum(lst)/float(len(lst))

class Abcd:
    def __init__(i,db="all",rx="all"):
        i.db = db; i.rx=rx;
        i.yes = i.no = 0
        i.known = {}; i.a= {}; i.b= {}; i.c= {}; i.d= {}
        global The
    def __call__(i,actual=None,predicted=None):
        return i.keep(actual,predicted)
    def tell(i,actual,predict):
        i.knowns(actual)
        i.knowns(predict)
        if actual == predict: i.yes += 1
        else                :  i.no += 1
        for x in  i.known:
            if actual == x:
                if  predict == actual: i.d[x] += 1
                else                 : i.b[x] += 1
            else:
                if  predict == x     : i.c[x] += 1
                else                 : i.a[x] += 1
    def knowns(i,x):
        if not x in i.known:
            i.known[x]= i.a[x]= i.b[x]= i.c[x]= i.d[x]= 0.0
        i.known[x] += 1
        if (i.known[x] == 1):
            i.a[x] = i.yes + i.no
    def header(i):

        if False:
            print "#",('{0:10s} {1:11s}  {2:4s}  {3:4s} {4:4s} '+ \
                       '{5:4s}{6:4s} {7:3s} {8:3s} {9:3s} '+ \
                       '{10:3s} {11:3s}{12:3s}{13:10s}').format(
                "db", "rx",
                "n", "a","b","c","d","acc","pd","pf","prec",
                "f","g","class")
            print '-'*100

    def ask(i):
        def p(y) : return int(100*y + 0.5)
        def n(y) : return int(y)
        def auto(x):
            try:
                return str(x)
            except ValueError:
                return x
        pd = pf = pn = prec = g = f = acc = 0
        scores = []
        for x in i.known:
            a= i.a[x]; b= i.b[x]; c= i.c[x]; d= i.d[x]
            if (b+d)    : pd   = d     / (b+d)
            if (a+c)    : pf   = c     / (a+c)
            if (a+c)    : pn   = (b+d) / (a+c)
            if (c+d)    : prec = d     / (c+d)
            if (1-pf+pd): g    = 2*(1-pf)*pd / (1-pf+pd)
            if (prec+pd): f    = 2*prec*pd/(prec+pd)
            if (i.yes + i.no): acc= i.yes/(i.yes+i.no)
            if False:
                print "#",('{0:10s} {1:10s} {2:4d} {3:4d} {4:4d} '+ \
                           '{5:4d} {6:4d} {7:4d} {8:3d} {9:3d} '+ \
                           '{10:3d} {11:3d} {12:3d} {13:10s}').format(i.db,
                                                                      i.rx,  n(b + d), n(a), n(b),n(c), n(d),
                                                                      p(acc), p(pd), p(pf), p(prec), p(f), p(g),auto(x))
            scores +=[[p(pd), p(pf), p(prec)]]  # e.g:[[100, 100, 74, 0], [0, 0, 74, 0]]
        return scores

        #print x,p(pd),p(prec)

def _Abcd(predicted, actual, threshold):
    predicted_txt = []
    abcd = Abcd(db='Training', rx='Testing')

    # for i,j in zip(predicted,actual):
    #     print i,j

    def isDef(x):
        return "Defective" if x >= threshold else "Non-Defective"
    for data in predicted:
        predicted_txt +=[isDef(data)]
    for act, pre in zip(actual, predicted_txt):
        abcd.tell(act, pre)
    abcd.header()
    score = abcd.ask()
    # pdb.set_trace()
    return score[-1]


def weitransform(list, threshold):
    result = []
    for l in list:
        if l > threshold: result.append("Defective")
        else: result.append("Non-Defective")
    return result




tera_decisions= [jmoo_decision("min_samples_split", 2, 20),
                  jmoo_decision("min_samples_leaf", 1, 20),
                  jmoo_decision("max_features", 0.01, 1),
                  jmoo_decision("max_depth", 1, 50),
                  jmoo_decision("threshold", 0, 1)
                  ]



tera_objectives = [jmoo_objective("pd", False),
                   jmoo_objective("pf", True),
                   jmoo_objective("prec", False),]


def readDataset(file, properties):
    prefix = "tera/"
    suffix = ".csv"
    finput = open(prefix + file + suffix, 'rb')
    reader = csv.reader(finput, delimiter=',')
    dataread = []
    try:
        k = properties.unusual_range_end
    except:
        k = 3
    for i,row in enumerate(reader):
        if i > 0: #ignore header row
            line = []
            for item in row[k:]:
                try:
                    line.append(float(item))
                except:
                    pass
            dataread.append(np.array(line))
    properties = row[:k]
    #print properties
    return np.array(dataread), properties

def evaluator(input, properties):

    # print input
    # print "Length: ", len(input)


    if properties.type != "default":
        mss = int(round(input[0]))
        msl = int(round(input[1]))
        mxf = float(input[2])
        md = int(input[3])
        threshold = float(input[4])
    else:
        threshold = 0.5

    assert(len(properties.training_dataset) == 1), "didn't assume"
    data_train = readDataset(properties.training_dataset[0], properties)
    data_test  = readDataset(properties.test_dataset, properties)


    #train the learner
    indep = np.array(map(lambda x: np.array(x[:-1]), data_train[0]))
    dep   = np.array(map(lambda x: np.array(x[-1:]), data_train[0]))


    from sklearn.tree import DecisionTreeRegressor
    if properties.type == "default":
        clf = DecisionTreeRegressor()
    else:
        clf = DecisionTreeRegressor(max_features=mxf, min_samples_split=mss, min_samples_leaf=msl, random_state= 1, max_depth= md)
    # random_state = 0, min_samples_split = mss, max_depth = md, max_leaf_nodes = mln, criterion = cri, min_samples_leaf = msl)
    clf.fit(indep, dep)

    #test the learner
    test_indep = np.array(map(lambda x: np.array(x[:-1]), data_test[0]))
    test_dep   = np.array(map(lambda x: np.array(x[-1:]), data_test[0]))
    t = clf.predict(test_indep)

    result = [i for i in t]
    result = [float(x) for x in result]

    scores = _Abcd(result, weitransform(test_dep, 0), threshold)
    return scores


class Properties:
    def __init__(self, name, test_file, train_file, type="Test"):
        self.dataset_name = name
        self.training_dataset = train_file
        self.test_dataset = test_file
        self.type = type

    def __str__(self):
        return self.dataset_name + str(self.training_dataset)


class xalan(jmoo_problem):
    def __init__(prob):
        prob.name = "Xalan"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "xalan-2.5", ["xalan-2.4"])
        prob.training = "xalan-2.4"
        prob.tuning = "xalan-2.5"
        prob.testing = "xalan-2.6"
    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]
    def evalConstraints(prob,input = None):
        return False #no constraints

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "xalan-2.6", ["xalan-2.4"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "xalan-2.6", ["xalan-2.4"], type="default"))
        return output
#ant

class xerces(jmoo_problem):
    def __init__(prob):
        prob.name = "xerces"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "xerces-1.3", ["xerces-1.2"])
        prob.training = "xerces-1.2"
        prob.tuning = "xerces-1.3"
        prob.testing = "xerces-1.4"
    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]
    def evalConstraints(prob,input = None):
        return False #no constraints


    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "xerces-1.4", ["xerces-1.2"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "xerces-1.4", ["xerces-1.2"], type="default"))
        return output

class velocity(jmoo_problem):
    def __init__(prob):
        prob.name = "Velocity"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "velocity-1.5", ["velocity-1.4"])
        prob.training = "velocity-1.4"
        prob.tuning = "velocity-1.5"
        prob.testing = "velocity-1.6"

    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]
    def evalConstraints(prob,input = None):
        return False #no constraints

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "velocity-1.6", ["velocity-1.4"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "velocity-1.6", ["velocity-1.4"], type="default"))
        return output


class synapse(jmoo_problem):
    def __init__(prob):
        prob.name = "synapse"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "synapse-1.1", ["synapse-1.0"])
        prob.training = "synapse-1.0"
        prob.tuning = "synapse-1.1"
        prob.testing = "synapse-1.2"

    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]
    def evalConstraints(prob,input = None):
        return False #no constraints

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "synapse-1.2", ["synapse-1.0"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "synapse-1.2", ["synapse-1.0"], type="default"))
        return output


class poi(jmoo_problem):
    def __init__(prob):
        prob.name = "poi"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "poi-2.0", ["poi-1.5"])
        prob.training = "poi-1.5"
        prob.tuning = "poi-2.0"
        prob.testing = "poi-2.5"
    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]

    def evalConstraints(prob,input = None):
        return False #no constraints

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "poi-2.5", ["poi-1.5"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "poi-2.5", ["poi-1.5"], type="default"))
        return output

class lucene(jmoo_problem):
    def __init__(prob):
        prob.name = "lucene"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "lucene-2.2", ["lucene-2.0"])
        prob.training = "lucene-2.0"
        prob.tuning = "lucene-2.2"
        prob.testing = "lucene-2.4"
    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]
    def evalConstraints(prob,input = None):
        return False #no constraints

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "lucene-2.4", ["lucene-2.0"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "lucene-2.4", ["lucene-2.0"], type="default"))
        return output

class jedit(jmoo_problem):
    def __init__(prob):
        prob.name = "jedit"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "jedit-4.0", ["jedit-3.2"])
        prob.training = "jedit-3.2"
        prob.tuning = "jedit-4.0"
        prob.testing = "jedit-4.1"
    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "jedit-4.1", ["jedit-3.2"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "jedit-4.1", ["jedit-3.2"], type="default"))
        return output

    def evalConstraints(prob,input = None):
        return False #no constraints

class ivy(jmoo_problem):
    def __init__(prob):
        prob.name = "ivy"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "ivy-1.4", ["ivy-1.1"])
        prob.training = "ivy-1.1"
        prob.tuning = "ivy-1.4"
        prob.testing = "ivy-2.0"
    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]
    def evalConstraints(prob,input = None):
        return False #no constraints

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "ivy-2.0", ["ivy-1.1"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "ivy-2.0", ["ivy-1.1"], type="default"))
        return output


class forrest(jmoo_problem):
    def __init__(prob):
        prob.name = "forrest"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "forrest-0.7", [ "forrest-0.6"])
        prob.training = "forrest-0.6"
        prob.tuning = "forrest-0.7"
        prob.testing = "forrest-0.8"
    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "forrest-0.8", ["forrest-0.6"]))
        return output

    def default(prob):
        output = evaluator(input, Properties(prob.name, "forrest-0.8", ["forrest-0.6"], type="default"))
        return output

    def evalConstraints(prob,input = None):
        return False #no constraints

class ant(jmoo_problem):
    def __init__(prob):
        prob.name = "ant"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "ant-1.4", ["ant-1.3"])
        prob.training = "ant-1.3"
        prob.tuning = "ant-1.4"
        prob.testing = "ant-1.5"

    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "ant-1.5", ["ant-1.3"]))
        return output
    def default(prob):
        output = evaluator(input, Properties(prob.name, "ant-1.5", ["ant-1.3"], type="default"))
        return output
    def evalConstraints(prob,input = None):
        return False  # no constraints


class camel(jmoo_problem):
    def __init__(prob):
        prob.name = "camel"
        prob.decisions = tera_decisions
        prob.objectives = tera_objectives
        prob.properties = Properties(prob.name, "camel-1.2", ["camel-1.0"])
        prob.training = "camel-1.0"
        prob.tuning = "camel-1.2"
        prob.testing = "camel-1.4"

    def evaluate(prob, input = None):
        if input:
            for i,decision in enumerate(prob.decisions):
                decision.value = input[i]
        input  = [decision.value for decision in prob.decisions]
        output = evaluator(input, prob.properties)
        prob.objectives[0].value = output[0]
        prob.objectives[1].value = output[1]
        prob.objectives[2].value = output[2]
        return [objective.value for objective in prob.objectives]

    def test(prob, input=None):
        if input is None:
            print "input parameter required"
            exit()
        output = evaluator(input, Properties(prob.name, "camel-1.4", ["camel-1.0"]))
        return output
    def default(prob):
        output = evaluator(input, Properties(prob.name, "camel-1.4", ["camel-1.0"], type="default"))
        return output


    def evalConstraints(prob,input = None):
        return False #no constraints

