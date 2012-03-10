nil = None
class Nil:
    def __init__(self):
        global nil
        assert nil is None
    def __repr__(self):
        return 'nil'
    def __eq__(self, other):
        return self is other
nil = Nil()
void = None

def _call(obj, arg, invoking_scope):
    if type(obj) is FunctionType:
        return obj(arg, invoking_scope)
    else:
        return obj.call(arg, invoking_scope)

class Pair:
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr
    def call(self, arg, invoking_scope):
        return _call(self.car, Pair(_call(self.cdr, arg, invoking_scope), nil), invoking_scope)
    def __eq__(self, other):
        return type(other) is Pair and self.car == other.car and self.cdr == other.cdr
    def __repr__(self):
        return '(Pair %s %s)' % (repr(self.car), repr(self.cdr))
    def __str__(self):
        return "(Pair %s %s)" % (str(self.car), str(self.cdr))
    def get(self, arg, scope):
        assert type(arg) is Pair
        assert eval_node(arg.cdr, scope) is nil
        key_node = arg.car
        assert type(key_node) is IdentifierNode
        identifier = key_node.identifier
        if identifier == 'car':
            return self.car
        elif identifier == 'cdr-slot':
            return self.cdr
        elif identifier == 'cdr':
            if type(self.cdr) is Promise:
                return self.cdr.get_value()
            else:
                return self.cdr
        else:
            raise Exception("Pair has no property %s" % identifier)

class Symbol:
    def __init__(self, value):
        assert type(value) is str
        self.value = value
    def __eq__(self, other):
        return type(other) is Symbol and self.value == other.value
    def __repr__(self):
        return "#%s" % self.value
    def __hash__(self):
        return hash(self.value)

class Object:
    def __init__(self):
        self.dict = {}
        self.proto = void
    def get_slot(self, slot):
        assert type(slot) is str
        if slot in self.dict:
            return self.dict[slot]
        elif self.proto is void:
            raise Exception("could not access slot %s" % slot)
        else:
            return self.proto.get_slot(slot)
    def get(self, arg, scope):
        assert type(arg) is Pair
        assert eval_node(arg.cdr, scope) is nil
        key_node = arg.car
        assert type(key_node) is IdentifierNode # TODO: maybe allow something else
        result = self.get_slot(key_node.identifier)
        if type(result) is Method:
            return BoundMethod(result, self)
        else:
            return result
    def set(self, arg, scope):
        assert type(arg) is Pair
        assert type(arg.cdr) is Pair
        assert eval_node(arg.cdr.cdr, scope) is nil
        key_node = arg.car
        assert type(key_node) is IdentifierNode # TODO: maybe allow something else
        value = eval_node(arg.cdr.car, scope)
        self.dict[key_node.identifier] = value
    def __eq__(self, other):
        return self is other
    def __repr__(self):
        if len(self.dict) == 0:
            return '{}'
        return '{ %s }' % ', '.join(['%s: %s' % (key, repr(value)) for key, value in self.dict.items()])

class Dictionary(Object):
    def __init__(self):
        super().__init__()
        self.data = {}
    def get(self, arg, scope):
        assert type(arg) is Pair
        key_node = arg.car
        if type(key_node) is IdentifierNode:
            super().get(arg, scope)

        assert eval_node(arg.cdr, scope) is nil
        return self.data[eval_node(key_node, scope)]
    def set(self, arg, scope):
        assert type(arg) is Pair
        key_node = arg.car
        if type(key_node) is IdentifierNode:
            super().set(arg, scope)
        assert type(arg.cdr) is Pair
        assert eval_node(arg.cdr.cdr, scope) is nil
        self.data[eval_node(key_node, scope)] = eval_node(arg.cdr.car, scope)
    def __eq__(self, other):
        return self is other
    def __repr__(self):
        if len(self.data) == 0:
            return '#{}'
        return '#{ %s }' % ', '.join(['%s: %s' % (repr(key), repr(value)) for key, value in self.data.items()])

class Promise:
    def __init__(self, arg, scope):
        assert type(arg) is Pair
        assert eval_node(arg.cdr, scope) is nil
        self.node = arg.car
        self.scope = scope
    def get_value(self):
        if 'value' not in self.__dict__:
            self.value = eval_node(self.node, self.scope)
            del self.node
            del self.scope
        return self.value

from reader import Node, IdentifierNode
from types import FunctionType
from evaluator import eval_node, Method, BoundMethod
