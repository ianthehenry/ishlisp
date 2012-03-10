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

def def_(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil
    assert type(arg.car) is IdentifierNode
    value = eval_node(arg.cdr.car, scope)
    scope.set(arg.car.identifier, value)
    return value

def redef(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil
    assert type(arg.car) is IdentifierNode
    value = eval_node(arg.cdr.car, scope)
    scope.set_recursive(arg.car.identifier, value)
    return value

def if_(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert type(arg.cdr.cdr) is Pair
    assert eval_node(arg.cdr.cdr.cdr, scope) is nil

    predicate_value = eval_node(arg.car, scope)
    then_node = arg.cdr.car
    else_node = arg.cdr.cdr.car

    # TODO: should perform boolean coercion here
    if predicate_value is True:
        return eval_node(then_node, scope)
    elif predicate_value is False:
        return eval_node(else_node, scope)
    else:
        raise Exception("I can't perform boolean coercion yet")

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
    assert type(arg) is Pair
    obj = eval_node(arg.car, scope)
    return obj.get(arg.cdr, scope)

def set(arg, scope):
    assert type(arg) is Pair
    obj = eval_node(arg.car, scope)
    return obj.set(arg.cdr, scope)

# TODO: it might be nice to allow keyword args that attached metadata to a function. maybe?
def function(arg, outer_scope):
    return Function(arg, outer_scope)

def method(arg, outer_scope):
    return Method(arg, outer_scope)

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
    elif type(arg) is ValueNode and isinstance(arg.value, Pattern):
        return eval_node(arg, scope)
    elif type(arg) is FormNode:
        car = eval_node(arg.car, scope) # TODO: add tests that verify this is not evaluated more than once
        arg = FormNode(ValueNode('CACHE', car), arg.cdr)
        if car is cons:
            return ConsPattern(arg.cdr, scope)
        elif car is list_:
            # there might be a more elegant way to do this. perhaps.
            if arg.cdr is nil:
                return ValuePattern(arg.cdr)
            else:
                return ConsPattern(arg.cdr, scope, True)
        elif car is slash:
            return _get_aliased_pattern(arg.cdr, scope)
        elif car is pattern_with_predicate:
            return pattern_with_predicate(arg.cdr, scope)
        elif car is pattern_with_default:
            return pattern_with_default(arg.cdr, scope)
        elif car is pattern:
            return pattern(arg.cdr, scope)

    return ValuePattern(eval_node(arg, scope))

def array(arg, scope):
    raise Exception("not yet implemented")

def slash(arg, scope):
    raise Exception("not yet implemented")

def get_slot(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil
    obj = eval_node(arg.car, scope)
    key = eval_node(arg.cdr.car, scope)
    assert type(key) is Symbol
    return obj.get_slot(key.value)

def function_shorthand(arg, scope):
    if arg is nil:
        return Function(Pair(ValueNode('_default_pattern', default_arguments_pattern_singleton), nil), scope)
    assert type(arg) is Pair
    return Function(Pair(ValueNode('_default_pattern', default_arguments_pattern_singleton), Pair(FormNode(arg.car, arg.cdr), nil)), scope)

def object(arg, scope):
    obj = Object()

    while arg is not nil:
        assert type(arg) is Pair
        slot = arg.car

        if type(slot) is FormNode:
            func = eval_node(slot.car, scope)
            slot = FormNode(ValueNode('CACHE', func), slot.cdr) # this ensures we only eval the car of the form once
            if func is cons:
                assert type(slot.cdr) is Pair
                obj.set(slot.cdr, scope)
            elif func is get:
                assert type(slot.cdr) is Pair
                assert type(slot.cdr.cdr) is Pair
                key_node = slot.cdr.cdr.car
                obj.set(Pair(key_node, Pair(slot, nil)), scope)
            else:
                raise Exception("I don't know what to do with that yet")
        elif type(slot) is IdentifierNode:
            obj.set(Pair(slot, Pair(slot, nil)), scope)
        else:
            raise Exception("syntax error!")

        arg = arg.cdr

    return obj

def bind(arg, scope):
    assert type(arg) is Pair
    assert type(arg.cdr) is Pair
    assert eval_node(arg.cdr.cdr, scope) is nil

    method = eval_node(arg.car, scope)
    if type(method) is BoundMethod:
        raise Exception("you cannot rebind a method...yet")
    assert type(method) is Method
    obj = eval_node(arg.cdr.car, scope)

    return BoundMethod(method, obj)

def dictionary(arg, scope):
    dct = Dictionary()

    while arg is not nil:
        assert type(arg) is Pair
        pair = eval_node(arg.car, scope)
        dct.set(Pair(ValueNode('CACHE', pair.car), Pair(ValueNode('CACHE', pair.cdr), nil)), scope)
        arg = arg.cdr

    return dct

from core import Pair, Object, nil, Symbol, Dictionary
from reader import FormNode, IdentifierNode, ValueNode
from evaluator import eval_node, Scope, Function, Method, BoundMethod
from patterns import *
from types import FunctionType

default_arguments_pattern_singleton = DefaultArgumentsPattern()
