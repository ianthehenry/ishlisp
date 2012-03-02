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

def fn(arg, scope):
    param_name = arg.car
    forms = arg.cdr
    assert type(param_name) is IdentifierNode
    assert type(forms) is FormNode
    param_name = param_name.identifier
    def lambduh(arg, outer_scope):
        nonlocal forms

        # evaluate our argument...to define a macro rather than a function, simply remove this statement. and the making-a-new-scope thing. whatever.
        if type(arg) is FormNode:
            arg = list_(arg, outer_scope)
        else:
            arg = eval_node(arg, outer_scope)

        inner_scope = Scope({param_name: arg}, outer_scope)
        return_value = nil
        while forms is not nil:
            return_value = eval_node(forms.car, inner_scope)
            forms = forms.cdr
        return return_value
    return lambduh
