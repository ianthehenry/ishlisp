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
    def __repr__(self):
        if type(self.cdr) is Pair:
            return "[%s %s" % (repr(self.car), self.cdr.continue_repr())
        elif self.cdr is nil:
            return "[%s]" % self.car
        else:
            return "[%s | %s]" % (repr(self.car), repr(self.cdr))
    def __str__(self):
        return "Pair [%s | %s]" % (str(self.car), str(self.cdr))
    def continue_repr(self):
        car, cdr = (self.car, self.cdr)

        if type(cdr) is Pair:
            return "%s %s" % (repr(car), cdr.continue_repr())
        elif cdr is nil:
            return "%s]" % repr(car)
        else:
            return "%s | %s]" % (repr(car), repr(cdr))
    def __eq__(self, other):
        return type(other) is Pair and self.car == other.car and self.cdr == other.cdr
