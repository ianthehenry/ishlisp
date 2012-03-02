from evaluator import eval_node, Pair, Scope
from reader import FormNode, nil, IdentifierNode, Node

def print_(arg, scope):
    print(eval_node(arg.car, scope))
    return nil

def add(arg, scope):
    return eval_node(arg.car, scope) + eval_node(arg.cdr.car, scope)

def id(arg, scope):
    return eval_node(arg, scope)

def car(arg, scope):
    return eval_node(arg.car, scope).car

def cdr(arg, scope):
    return eval_node(arg.car, scope).cdr

def list_(arg, scope):
    if arg is nil:
        return nil
    if type(arg) is not Pair:
        raise Exception('cannot have a cdr without a car')
    return Pair(eval_node(arg.car, scope), eval_node(arg.cdr, scope))

def fn(declaration, outer_scope):
    param_name = declaration.car
    assert type(param_name) is IdentifierNode # will be a pattern soon
    assert type(declaration.cdr) is Pair
    param_name = param_name.identifier

    def lambduh(arg, invoking_scope):
        forms = declaration.cdr
        inner_scope = Scope({param_name: eval_node(arg, invoking_scope)}, outer_scope)
        return_value = nil
        while forms is not nil:
            return_value = eval_node(forms.car, inner_scope)
            forms = forms.cdr
        return return_value
    return lambduh
