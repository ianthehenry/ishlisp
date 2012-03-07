# imports at bottom of file

def print_(arg, scope):
    print(eval_node(arg.car, scope))
    return nil

def add(arg, scope):
    return eval_node(arg.car, scope) + eval_node(arg.cdr.car, scope)

def cons(arg, scope):
    car = arg.car
    cdr = arg.cdr.car
    return Pair(eval_node(car, scope), eval_node(cdr, scope))

def even(arg, scope):
    assert type(arg) is Pair
    assert eval_node(arg.cdr, scope) is nil
    arg = eval_node(arg.car, scope)
    assert type(arg) is int
    return arg % 2 == 0

def odd(arg, scope):
    return not even(arg, scope)

def id(arg, scope):
    assert type(arg) is Pair
    assert eval_node(arg.cdr, scope) is nil
    return eval_node(arg.car, scope)

def car(arg, scope):
    assert type(arg) is Pair
    assert eval_node(arg.cdr, scope) is nil
    return eval_node(arg.car, scope).car

def cdr(arg, scope):
    assert type(arg) is Pair
    assert eval_node(arg.cdr, scope) is nil
    return eval_node(arg.car, scope).cdr

def call(arg, scope):
    assert type(arg) is Pair
    function = eval_node(arg.car, scope)
    assert type(arg.cdr) is Pair
    return function(arg.cdr, scope)

def apply(arg, scope):
    assert type(arg) is Pair
    function = eval_node(arg.car, scope)
    assert type(arg.cdr) is Pair
    argument = eval_node(arg.cdr.car, scope)
    assert type(argument) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil
    return function(argument, scope)

def curry(arg, scope):
    assert type(arg) is Pair
    function = eval_node(arg.car, scope)
    assert type(arg.cdr) is Pair
    arguments = eval_node(arg.cdr, scope)
    last = arguments
    while last.cdr is not nil:
        assert type(last) is Pair
        last = last.cdr

    def curried(more_args, scope):
        assert type(more_args) is Pair
        last.cdr = more_args
        return function(arguments, scope)

    return curried

def list_(arg, scope):
    if arg is nil:
        return nil
    if type(arg) is not Pair:
        raise Exception('cannot have a cdr without a car')
    return Pair(eval_node(arg.car, scope), eval_node(arg.cdr, scope))

def get(arg, scope):
    raise Exception("not yet implemented")

# TODO: it might be nice to allow keyword args that attached metadata to a function. maybe?
def fn(declaration, outer_scope):
    param_pattern = pattern(declaration.car, outer_scope)
    assert type(declaration.cdr) is Pair or declaration.cdr is nil
    return Function(param_pattern, declaration.cdr, outer_scope)

def match(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil
    pattern = eval_node(arg.car, scope)
    target = eval_node(arg.cdr.car, scope)
    new_scope = Scope({}, scope)
    return pattern.match(target, new_scope)

def pattern_with_predicate(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil
    base_pattern = pattern(arg.car, scope)

    predicate_node = arg.cdr.car
    # if it's a FormNode, turn it into a mini function.
    #   if it's a Type, its predicate is curryauto-add the instance? predicate
    #   if it's a function, use it as the predicate
    # for now we will insist that it be a predicate function

    predicate = eval_node(arg.cdr.car, scope)
    assert type(predicate) is FunctionType

    return PredicatedPattern(base_pattern, predicate)

def pattern_with_default(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil
    base_pattern = pattern(arg.car, scope)
    value_node = arg.cdr.car

    return DefaultedPattern(base_pattern, eval_node(value_node, scope))

def _get_aliased_pattern(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil
    left_pattern = pattern(arg.car, scope)
    right_pattern = pattern(arg.cdr.car, scope)

    return AliasedPattern(left_pattern, right_pattern)

def pattern(arg, scope):
    assert arg is nil or type(arg) is Pair or isinstance(arg, Node)

    if arg is nil:
        return ValuePattern(nil, scope)
    if type(arg) is Pair:
        arg = arg.car

    if type(arg) is IdentifierNode:
        return IdentifierPattern(arg, scope)

    if type(arg) is FormNode:
        car = eval_node(arg.car, scope)
        if car is cons:
            return ConsPattern(arg.cdr, scope)
        elif car is list_:
            return ConsPattern(arg.cdr, scope, True)
        elif car is slash:
            return _get_aliased_pattern(arg.cdr, scope)
        elif car is pattern_with_predicate:
            return pattern_with_predicate(arg.cdr, scope)
        elif car is pattern_with_default:
            return pattern_with_default(arg.cdr, scope)
        elif car is pattern:
            return pattern(arg.cdr, scope)
        elif car is default_arguments_pattern:
            return default_arguments_pattern(arg.cdr, scope)

    return ValuePattern(eval_node(arg, scope))

def array(arg, scope):
    raise Exception("not yet implemented")

def slash(arg, scope):
    raise Exception("not yet implemented")

def default_arguments_pattern(arg, scope):
    return default_arguments_pattern_singleton

from core import Pair, nil
from reader import FormNode, IdentifierNode, ValueNode
from evaluator import eval_node, Scope, Function
from patterns import *
from types import FunctionType

default_arguments_pattern_singleton = DefaultArgumentsPattern()
