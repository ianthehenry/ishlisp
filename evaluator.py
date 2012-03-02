from reader import read, FormNode, IdentifierNode, NumericLiteralNode
from types import FunctionType
from core import Pair, nil
# specials is imported below

class Scope:
    def __init__(self, dict, parent):
        self.dict = dict
        self.parent = parent
    def get(self, identifier):
        if identifier in self.dict:
            return self.dict[identifier]
        if self.parent is None:
            raise Exception("identifier '%s' is not in scope" % identifier)
        return self.parent.get(identifier)

def eval_node(node, scope):
    if node is nil:
        return nil

    if type(node) is Pair:
        return Pair(eval_node(node.car, scope), eval_node(node.cdr, scope))

    if type(node) is FormNode:
        fn = eval_node(node.car, scope)
        assert type(fn) is FunctionType
        return fn(node.cdr, scope)
    elif type(node) is IdentifierNode:
        return scope.get(node.identifier)
    elif type(node) is NumericLiteralNode:
        return node.num
    else:
        raise Exception("I don't know how to eval %s (%s)" % (str(node), type(node)))

import specials # we have to do this here because it relies on the eval_node function

root = Scope({
    'print': specials.print_,
    'add': specials.add,
    'id': specials.id,
    'list': specials.list_,
    'car': specials.car,
    'cdr': specials.cdr,
    'fn': specials.fn,
    'nil': nil
}, None)

def isheval(code, scope = root):
    ret_value = nil
    for node in read(code):
        ret_value = eval_node(node, scope)
    return ret_value
