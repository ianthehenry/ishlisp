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
        if target is None:
            return False
        scope.set(self.identifier, target)
        return True
    def __repr__(self):
        return "(IdentifierPattern %s)" % self.identifier
    def __eq__(self, other):
        return type(other) is IdentifierPattern and self.identifier == other.identifier

class ValuePattern(Pattern):
    def __init__(self, node, scope):
        assert node is nil or isinstance(node, Node)
        self.value = eval_node(node, scope)
    def match(self, target, scope):
        return self.value == target
    def __repr__(self):
        return "(ValuePattern %s)" % repr(self.value)
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
# We could just make a ListPattern, but it's not necessary.
class ConsPattern(Pattern):
    def __init__(self, pair, scope, recursive = False):
        assert type(pair) is Pair
        self.car_pattern = specials.pattern(pair.car, scope)
        if recursive:
            self.cdr_pattern = rec_pattern(pair.cdr, scope)
        else:
            self.cdr_pattern = specials.pattern(pair.cdr, scope)
    def match(self, target, scope):
        if target is nil:
            return (self.car_pattern.match(None, scope) and self.cdr_pattern.match(None, scope))
        if type(target) is not Pair:
            return False
        return self.car_pattern.match(target.car, scope) and self.cdr_pattern.match(target.cdr, scope)
    def __repr__(self):
        return "(ConsPattern %s %s)" % (repr(self.car_pattern), repr(self.cdr_pattern))
    def __eq__(self, other):
        return type(other) is ConsPattern and self.car_pattern == other.car_pattern and self.cdr_pattern == other.cdr_pattern

class PredicatedPattern(Pattern):
    def __init__(self, pattern, predicate):
        self.pattern = pattern
        assert type(self.pattern) is not DefaultedPattern, "you can't apply a predicate to a defaulted pattern. it just doesn't make sense."
        self.predicate = predicate
    def __repr__(self):
        return "(PredicatedPattern %s %s)" % (repr(self.pattern), repr(self.predicate))
    def match(self, target, scope):
        return self.pattern.match(target, scope) and self.predicate(Pair(target, nil), None) is True
    def __eq__(self, other):
        return type(other) is PredicatedPattern and self.pattern == other.pattern and self.predicate == other.predicate

class DefaultedPattern(IdentifierPattern):
    def __init__(self, pattern, default_value):
        self.pattern = pattern

        # Basically, it only makes sense to apply a default value to an identifier pattern or a
        # predicated identifier pattern (or a predicated predicated identifier pattern, etc).
        # We don't *need* to assert this, but it doesn't hurt.
        # Actually, it might be kind of convenient. Consider `[a b c]=[1 2 3]`. If any part of that
        # match fails, `a`, `b`, and `c` are still bound. It's similar to `[a=1 b=2 c=3]`, except
        # that it will still succeed even if the thing passed is not a list at all, or has more
        # than three elements. I guess it's more like `[a=1 b=2 c=3 | -]`, but still not the same.
        if type(self.pattern) is not IdentifierPattern:
            p = self.pattern
            while type(p) is not IdentifierPattern:
                assert type(p) is PredicatedPattern, "it doesn't make any sense to apply a default value to that. what's wrong with you?"
                p = p.pattern
        self.default_value = default_value

        scope = Scope({}, None)
        # TODO: performing this sanity check is potentially dangerous. What if self.pattern is a PredicatedPattern
        # whose predicate has side-effects? Then it would be invoked once. Right now I think it's okay to just
        # document this behavior, but in the future this should be removed.
        # In fact, this *can't* work, since the pattern may be a predicated pattern whose predicate relies on a
        # value bound previously in the course of the matching. So there.
        assert self.pattern.match(self.default_value, scope), "you can't set a default that doesn't match the pattern itself"

    def match(self, target, scope):
        if target is None:
            return self.pattern.match(self.default_value, scope)
        else:
            # TODO: Re-matching the pattern like this may have some weird effects.
            # Say you have `[a [b::(gt b a) a c]=[10 20 30]]` matching against `[1 [2 100]]`.
            # On the first check, `b` succeeds (`a` is 1 and `b` is 2) and is bound to 2. Then
            # `a` is rebound to 20.
            # Potential solutions:
            #   - Buffer any changes made by the first check and only apply them if the match succeeds.
            #   - Don't allow rebinding of a name within a pattern match.
            #   - Document this.
            # Also, if there are predicates with side-effects that get re-evaluated, that might
            # cause some unexpected behavior. This we cannot avoid -- the programmer simply needs
            # to be aware of it. Or we could re-evaluate in a special "don't care about predicates"
            # mode when we apply default values. That...that's actually a really good idea.
            return self.pattern.match(target, scope) or self.pattern.match(self.default_value, scope)
    def __repr__(self):
        return "(DefaultedPattern %s %s)" % (repr(self.pattern), repr(self.default_value))
    def __eq__(self, other):
        return type(other) is DefaultedPattern and self.pattern == other.pattern and self.default_value == other.default_value
