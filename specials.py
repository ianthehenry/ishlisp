from evaluator import eval_node, Pair
from reader import FormNode, nil

def print_(arg, scope):
    print(eval_node(arg[0], scope))

def add(arg, scope):
    return eval_node(arg[0], scope) + eval_node(arg[1][0], scope)

def id(arg, scope):
    return eval_node(arg[0])

def pair(arg, scope):
    form_node = arg[0]
    assert type(form_node) is FormNode
    assert arg[1] is nil

    return Pair(eval_node(form_node.car, scope), eval_node(form_node.cdr, scope))
