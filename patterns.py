from evaluator import Scope, eval_node
from reader import Node, IdentifierNode, FormNode
from core import nil, Pair
import specials

class Pattern:
    pass

class IdentifierPattern(Pattern):
    def __init__(self, identifier_node, scope):
        assert type(identifier_node) is IdentifierNode
        self.identifier = identifier_node.identifier
    def match(self, target, scope):
        scope.set(self.identifier, target)
        return True
    def __repr__(self):
        return "(IdentifierPattern %s)" % self.identifier

class ValuePattern(Pattern):
    def __init__(self, node, scope):
        assert node is nil or isinstance(node, Node)
        self.value = eval_node(node, scope)

    def match(self, target, scope):
        return self.value == target

    def __repr__(self):
        return "(ValuePattern %s)" % repr(self.value)

# a helper for ConsPattern
def rec_pattern(arg, scope):
    if type(arg) is Pair:
        return ConsPattern(arg, scope, True)
    else:
        if arg is nil:
            return ValuePattern(nil, None)
        else:
            return specials.pattern(arg, scope)

# the recursive thing is just a convenience so that (list 1 2) will expand to multuple ConsPatterns.
# We could just make a ListPatter instead.
class ConsPattern(Pattern):
    def __init__(self, pair, scope, recursive = False):
        assert type(pair) is Pair
        self.car_pattern = specials.pattern(pair.car, scope)
        if recursive:
            self.cdr_pattern = rec_pattern(pair.cdr, scope)
        else:
            self.cdr_pattern = specials.pattern(pair.cdr, scope)
    def match(self, target, scope):
        if type(target) is not Pair:
            return False
        return self.car_pattern.match(target.car, scope) and self.cdr_pattern.match(target.cdr, scope)
    def __repr__(self):
        return "(ConsPattern %s %s)" % (repr(self.car_pattern), repr(self.cdr_pattern))
