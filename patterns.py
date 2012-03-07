from evaluator import Scope, eval_node
from reader import Node, IdentifierNode, FormNode
from core import nil, Pair
import specials

class Pattern:
    def call(self, arg, scope):
        assert type(arg) is Pair or arg is nil
        if arg is nil:
            target = None
        else:
            assert eval_node(arg.cdr, scope) is nil
            target = eval_node(arg.car, scope)
        if not self.match(target, scope, True):
            # return False
            raise Exception("pattern failed to match")
        return True

class IdentifierPattern(Pattern):
    def __init__(self, identifier_node, scope):
        assert type(identifier_node) is IdentifierNode
        self.identifier = identifier_node.identifier
    def match(self, target, scope, recursive = False):
        if target is None:
            return False
        if recursive:
            scope.set_recursive(self.identifier, target)
        else:
            scope.set(self.identifier, target)
        return True
    def __repr__(self):
        return "(IdentifierPattern %s)" % self.identifier
    def nice_repr(self):
        return repr(self)
    def __eq__(self, other):
        return type(other) is IdentifierPattern and self.identifier == other.identifier

class ValuePattern(Pattern):
    def __init__(self, node, scope):
        assert node is nil or isinstance(node, Node)
        self.value = eval_node(node, scope)
    def match(self, target, scope, recursive = False):
        return self.value == target
    def __repr__(self):
        return "(ValuePattern %s)" % repr(self.value)
    def nice_repr(self):
        return repr(self)
    def __eq__(self, other):
        return type(other) is ValuePattern and self.value == other.value

# a helper for ConsPattern
def rec_pattern(arg, scope):
    if type(arg) is Pair:
        return ConsPattern(arg, scope, True)
    else:
        if arg is nil:
            return ValuePattern(nil, None)
        else:
            return specials.pattern(arg, scope)

# The recursive thing is just a convenience so that (list 1 2) will expand to multiple ConsPatterns.
class ConsPattern(Pattern):
    def __init__(self, pair, scope, recursive = False):
        assert type(pair) is Pair
        self.car_pattern = specials.pattern(pair.car, scope)
        if recursive:
            self.cdr_pattern = rec_pattern(pair.cdr, scope)
        else:
            self.cdr_pattern = specials.pattern(pair.cdr, scope)
    def match(self, target, scope, recursive = False):
        if target is nil or target is None:
            return self.car_pattern.match(None, scope, recursive) and self.cdr_pattern.match(target, scope, recursive)
        if type(target) is not Pair:
            return False
        return self.car_pattern.match(target.car, scope, recursive) and self.cdr_pattern.match(target.cdr, scope, recursive)
    def __repr__(self):
        return "(ConsPattern %s %s)" % (repr(self.car_pattern), repr(self.cdr_pattern))
    def nice_repr(self):
        return repr(self)
    def __eq__(self, other):
        return type(other) is ConsPattern and self.car_pattern == other.car_pattern and self.cdr_pattern == other.cdr_pattern

class PredicatedPattern(Pattern):
    def __init__(self, pattern, predicate):
        self.pattern = pattern
        assert type(self.pattern) is not DefaultedPattern, "you can't apply a predicate to a defaulted pattern. it just doesn't make sense."
        self.predicate = predicate
    def match(self, target, scope, recursive = False):
        return self.pattern.match(target, scope, recursive) and self.predicate(Pair(target, nil), None) is True
    def __repr__(self):
        return "(PredicatedPattern %s %s)" % (repr(self.pattern), repr(self.predicate))
    def nice_repr(self):
        return repr(self)
    def __eq__(self, other):
        return type(other) is PredicatedPattern and self.pattern == other.pattern and self.predicate == other.predicate

class DefaultedPattern(IdentifierPattern):
    def __init__(self, pattern, default_value):
        assert isinstance(pattern, Pattern)
        self.pattern = pattern
        self.default_value = default_value
        scope = Scope({}, None)
    def match(self, target, scope, recursive = False):
        if target is None:
            return self.pattern.match(self.default_value, scope, recursive)
        else:
            return self.pattern.match(target, scope) or self.pattern.match(self.default_value, scope)
    def __repr__(self):
        return "(DefaultedPattern %s %s)" % (repr(self.pattern), repr(self.default_value))
    def nice_repr(self):
        return repr(self)
    def __eq__(self, other):
        return type(other) is DefaultedPattern and self.pattern == other.pattern and self.default_value == other.default_value
