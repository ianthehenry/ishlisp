from core import Pair, nil, Symbol
from reader import read, FormNode, IdentifierNode, NumericLiteralNode, ValueNode, Node, SymbolLiteralNode
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
    def has(self, identifier):
        assert type(identifier) is str
        return identifier in self.dict
    def set_recursive(self, identifier, value, top = True):
        if self.has(identifier):
            self.set(identifier, value)
            return True
        elif self.parent is None:
            if top:
                self.set(identifier, value)
                return True
            else:
                return False
        elif self.parent.set_recursive(identifier, value, False):
            pass
        elif top:
            self.set(identifier, value)
        return True

    def identifiers(self):
        return self.dict.keys()

class Function:
    def __init__(self, arg, scope):
        assert type(arg) is Pair
        assert type(arg.cdr) is Pair or arg.cdr is nil
        self.pattern = specials.pattern(arg.car, scope)
        self.forms = arg.cdr
        self.scope = scope
    def __repr__(self):
        return "(fn %s %s)" % (self.pattern.nice_repr(), repr(self.forms))
    def call(self, arg, invoking_scope, initial_scope_contents = None):
        new_scope = Scope(initial_scope_contents or {}, self.scope)
        evaled_arg = eval_node(arg, invoking_scope)
        if not self.pattern.match(evaled_arg, new_scope):
            raise Exception("pattern did not match. pattern: '%s' actual: '%s'" % (self.pattern.nice_repr(), repr(evaled_arg)))
        val = nil # TODO: should be void
        if not new_scope.has('-'):
            new_scope.set('-', val)
        forms = self.forms
        while forms is not nil:
            val = eval_node(forms.car, new_scope)
            new_scope.set('-', val)
            forms = forms.cdr
        return val

class Method(Function):
    def __repr__(self):
        return "(md %s %s)" % (self.pattern.nice_repr(), repr(self.forms))
    def call(self, arg, invoking_scope):
        raise Exception("an unbound method cannot be invoked")

class BoundMethod:
    def __init__(self, arg, scope):
        assert type(arg) is Pair
        assert type(arg.cdr) is Pair
        assert eval_node(arg.cdr.cdr, scope) is nil

        self.method = eval_node(arg.car, scope)
        if type(self.method) is BoundMethod:
            raise Exception("you cannot rebind a method...yet")
        assert type(self.method) is Method
        self.obj = eval_node(arg.cdr.car, scope)
    def __repr__(self):
        return "(BoundMethod %s %s)" % (repr(self.method), repr(self.obj))
    def call(self, arg, invoking_scope):
        return super(Method, self.method).call(arg, invoking_scope, {'this': self.obj})

def eval_node(node, scope):
    if type(node) is Pair:
        return Pair(eval_node(node.car, scope), eval_node(node.cdr, scope))

    # we're re-evaluating something that's already been evaluated. this might be a terrible idea.
    # currently used by the apply and curry builtins to pre-apply arguments before calling a built-in function
    # should just use ValueNodes in all cases
    if not isinstance(node, Node):
        return node

    if type(node) is FormNode:
        fn = eval_node(node.car, scope)
        if type(fn) is FunctionType:
            return fn(node.cdr, scope)
        else:
            return fn.call(node.cdr, scope)
    elif type(node) is IdentifierNode:
        return scope.get(node.identifier)
    elif type(node) is NumericLiteralNode:
        return int(node.value)
    elif type(node) is SymbolLiteralNode:
        return Symbol(node.value)
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
    'set': specials.set,
    'car': specials.car,
    'cdr': specials.cdr,
    'function': specials.function,
    'fn': specials.function,
    'method': specials.method,
    'md': specials.method,
    'bind': specials.bind,
    'pattern': specials.pattern,
    'pattern-with-predicate': specials.pattern_with_predicate,
    'pattern-with-default': specials.pattern_with_default,
    'match?': specials.match,
    'call': specials.call,
    'apply': specials.apply,
    'curry': specials.curry,
    'even?': specials.even,
    'odd?': specials.odd,
    'object': specials.object,
    'dictionary': specials.dictionary,
    'nil': nil
}, None)

def isheval(code, scope = root):
    ret_value = nil
    for node in read(code):
        ret_value = eval_node(node, scope)
    return ret_value

from patterns import Pattern
