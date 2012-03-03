from core import Pair, nil
from reader import read, FormNode, IdentifierNode, NumericLiteralNode, ValueNode, Node
from types import FunctionType
import specials

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
    def set(self, identifier, value):
        assert type(identifier) is str
        self.dict[identifier] = value
    def identifiers(self):
        return self.dict.keys()

def eval_node(node, scope):
    if type(node) is Pair:
        return Pair(eval_node(node.car, scope), eval_node(node.cdr, scope))

    # we're re-evaluating something that's already been evaluated. this might be a terrible idea.
    # currently used by the apply and curry builtins to pre-apply arguments before calling a built-in function
    if not isinstance(node, Node):
        return node

    if type(node) is FormNode:
        fn = eval_node(node.car, scope)
        assert type(fn) is FunctionType
        return fn(node.cdr, scope)
    elif type(node) is IdentifierNode:
        return scope.get(node.identifier)
    elif type(node) is NumericLiteralNode:
        return node.num
    elif type(node) is ValueNode:
        return node.value
    else:
        raise Exception("I don't know how to eval %s (%s)" % (str(node), type(node)))

root = Scope({
    'print': specials.print_,
    'add': specials.add,
    'id': specials.id,
    'list': specials.list_,
    'cons': specials.cons,
    'get': specials.get,
    'car': specials.car,
    'cdr': specials.cdr,
    'fn': specials.fn,
    'pattern': specials.pattern,
    'match': specials.match,
    'call': specials.call,
    'apply': specials.apply,
    'curry': specials.curry,
    'nil': nil
}, None)

def isheval(code, scope = root):
    ret_value = nil
    for node in read(code):
        ret_value = eval_node(node, scope)
    return ret_value
