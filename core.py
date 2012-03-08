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

class Pair:
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr
    def __eq__(self, other):
        return type(other) is Pair and self.car == other.car and self.cdr == other.cdr
    def __repr__(self):
        return '(Pair %s %s)' % (repr(self.car), repr(self.cdr))
    def __str__(self):
        return "(Pair %s %s)" % (str(self.car), str(self.cdr))

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
        self.proto = None
    def get(self, key):
        assert type(key) is IdentifierNode # TODO: should eventually allow resolution to something else
        return self.dict[key.identifier]
    def set(self, key, value):
        assert type(key) is str
        self.dict[key] = value
    def __eq__(self, other):
        return self is other
    def __repr__(self):
        if len(self.dict) == 0:
            return '{}'
        return '{ %s }' % ', '.join(['%s: %s' % (key, repr(value)) for key, value in self.dict.items()])

from reader import IdentifierNode
