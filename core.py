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
