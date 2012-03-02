from evaluator import eval_node, Pair, Scope
from reader import FormNode, nil, IdentifierNode, Node

def print_(arg, scope):
    print(eval_node(arg.car, scope))
    return nil

def add(arg, scope):
    return eval_node(arg.car, scope) + eval_node(arg.cdr.car, scope)

def id(arg, scope):
    print()
    print(str(arg))

    return eval_node(arg, scope)

def car(arg, scope):
    return eval_node(arg.car, scope).car

def cdr(arg, scope):
    return eval_node(arg.car, scope).cdr

def list_(arg, scope):
    if arg is nil:
        return nil
    if type(arg) is not FormNode:
        raise Exception('cannot have a cdr without a car')
    return Pair(eval_node(arg.car, scope), list_(arg.cdr, scope) if type(arg.cdr) is FormNode else eval_node(arg.cdr, scope))

def fn(arg, scope):
    param_name = arg.car
    forms = arg.cdr
    assert type(param_name) is IdentifierNode
    assert type(forms) is FormNode
    param_name = param_name.identifier
    def lambduh(arg, outer_scope):
        nonlocal forms

        inner_scope = Scope({param_name: eval_node(arg, outer_scope)}, outer_scope)
        return_value = nil
        while forms is not nil:
            return_value = eval_node(forms.car, inner_scope)
            forms = forms.cdr
        return return_value
    return lambduh
