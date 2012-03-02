from reader import nil, read, FormNode, IdentifierNode, NumericLiteralNode
from types import FunctionType
# specials is imported below

class Pair:
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def __repr__(self):
        if type(self.cdr) is Pair:
            return "[%s %s" % (repr(self.car), self.cdr.continue_repr())
        elif self.cdr is nil:
            return "[%s]" % self.car
        else:
            return "[%s | %s]" % (repr(self.car), repr(self.cdr))

    def continue_repr(self):
        car, cdr = (self.car, self.cdr)

        if type(cdr) is Pair:
            return "%s %s" % (repr(car), cdr.continue_repr())
        elif cdr is nil:
            return "%s]" % repr(car)
        else:
            return "%s | %s]" % (repr(car), repr(cdr))

class Scope:
    def __init__(self, dict, parent):
        self.dict = dict
        self.parent = parent
    def get(self, identifier):
        if identifier in self.dict:
            return self.dict[identifier]
        if self.parent is None:
            print(self.dict)
            raise Exception("identifier '%s' is not in scope" % identifier)
        return self.parent.get(identifier)

def eval_node(node, scope):
    # it might be nicer to represent FormNodes as actual pairs, not tuples, so that we don't have to do this
    if node is nil:
        return nil
    elif type(node) is tuple:
        return Pair(node[0], eval_node(node[1], scope))

    if type(node) is FormNode:
        fn = eval_node(node.car, scope)
        assert type(fn) is FunctionType
        return fn(node.cdr, scope)
    elif type(node) is IdentifierNode:
        return scope.get(node.identifier)
    elif type(node) is NumericLiteralNode:
        return node.num
    else:
        raise Exception("I don't know how to eval %s (%s)" % (repr(node), type(node)))

import specials # we have to do this here because it relies on the eval_node function

root = Scope({
    'print': specials.print_,
    'add': specials.add,
    'id': specials.id,
    'list': specials.list_,
    'car': specials.car,
    'cdr': specials.cdr,
    'nil': nil
}, None)

def isheval(code):
    for node in read(code):
        eval_node(node, root)
    return 'if you were expecting a return value here you should probs implement that'
