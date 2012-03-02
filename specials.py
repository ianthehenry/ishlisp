from evaluator import eval_node, Pair, Scope
from reader import FormNode, nil, IdentifierNode, Node

def print_(arg, scope):
    print(eval_node(arg.car, scope))

def add(arg, scope):
    return eval_node(arg.car, scope) + eval_node(arg.cdr.car, scope)

def id(arg, scope):
    return eval_node(arg.car, scope)

def car(arg, scope):
    return eval_node(arg.car, scope).car

def cdr(arg, scope):
    return eval_node(arg.car, scope).cdr

def list_(arg, scope):
    if arg is nil:
        return nil
    if type(arg) is not FormNode:
        raise Exception('cannot have a cdr without a car')
    return Pair(eval_node(arg.car, scope), list_(arg.cdr, scope) if type(arg.cdr) is FormNode else arg.cdr)
