import unittest
from core import nil, void, Pair
from reader import lex, read, parse_forms, FormNode, BINARY_OPERATORS, UNARY_OPERATORS, PAIR_CDR_TOKEN, NumericLiteralNode, IdentifierNode, expand_binary_operators, expand_unary_operators, ValueNode
from evaluator import isheval, root, Scope, Function
from types import LambdaType, FunctionType
import specials

def read_one(code):
    return read(code)[0]

def Forms(*nodes):
    return parse_forms(nodes)

class Tests(unittest.TestCase):
    def _repr_is_homoiconic(self, code):
        self.assertEqual(code, repr(read_one(code)))

    def _test_pattern_fails(self, pattern_code, target_code, initial_scope = None):
        if initial_scope is None:
            initial_scope = {}
        scope = Scope(initial_scope, root)
        self.assertFalse(isheval(pattern_code).match(isheval(target_code), scope))

    def _test_pattern(self, pattern_code, target_code, expected_scope, initial_scope = None):
        if initial_scope is None:
            initial_scope = {}
        scope = Scope(initial_scope, root)
        pattern = isheval(pattern_code)
        self.assertTrue(pattern.match(isheval(target_code), scope))
        self.assertEqual(scope.identifiers(), expected_scope.keys())
        for key in expected_scope:
            self.assertEqual(expected_scope[key], scope.get(key))

    def test_scope(self):
        parent = Scope({}, None)
        parent.set('foo', 10)
        parent.set('bar', 20)

        child = Scope({}, parent)
        child.set('foo', 15)
        self.assertTrue(child.set_recursive('bar', 25))

        self.assertEqual(10, parent.get('foo'))
        self.assertEqual(25, parent.get('bar'))
        self.assertEqual(15, child.get('foo'))
        self.assertEqual(25, parent.get('bar'))
        self.assertRaises(Exception, child.get, 'baz')


    # repr tests

    def test_list_repr_empty_lists_are_nil(self):
        self.assertEqual('(_list)', repr(read_one('[]')))
    def test_form_node_repr(self):
        self._repr_is_homoiconic('(a)')
        self._repr_is_homoiconic('(a | b)')
        self._repr_is_homoiconic('(a b | 3)')
        self._repr_is_homoiconic('(a b 3)')
        self._repr_is_homoiconic('(a (b))')
        self._repr_is_homoiconic('(a | (b))')
        self.assertRaises(Exception, read, '(|)')
        self.assertRaises(Exception, read, '(a |)')
        self.assertRaises(Exception, read, '(| a)')
        self.assertRaises(Exception, read, '(a | b 3)')

    # eval tests

    def test_eval(self):
        self.assertEqual(11, isheval('(add 5 6)'))
        self.assertEqual(8, isheval('(add 5 (add 1 2))'))
        self.assertEqual(18, isheval('(add (add 5 10) (add 1 2))'))
    def test_eval_void(self):
        self.assertEqual(void, isheval('()'))
    def test_eval_builtin_id(self):
        self.assertEqual(2, isheval('(id 2)'))
        self.assertEqual(5, isheval('(id (add 2 3))'))
        self.assertEqual(Pair(1, nil), isheval('(id (list 1))'))
        self.assertEqual(Pair(1, nil), isheval('(id [1])'))
        self.assertEqual(Pair(1, 2), isheval('(id [1 | 2])'))
        self.assertEqual(1, isheval('(id 1)'))
        self.assertEqual(20, isheval('((id id) 20)'))
    def test_eval_square_brackets(self):
        self.assertEqual(Pair(1, nil), isheval('[1]'))
        self.assertEqual(Pair(1, Pair(2, Pair(3, nil))), isheval('[1 2 3]'))
        self.assertEqual(Pair(1, 2), isheval('[1 | 2]'))
        self.assertEqual(Pair(1, Pair(2, 3)), isheval('[1 2 | 3]'))
        self.assertEqual(Pair(10, nil), isheval('[(add 5 5)]'))
        self.assertEqual(Pair(10, 20), isheval('[(add 5 5) | (add 10 10)]'))
    def test_eval_list_special_form(self):
        self.assertEqual(Pair(7, Pair(8, Pair(9, nil))), isheval('(list 7 8 9)'))
        self.assertEqual(Pair(10, 20), isheval('(list 10 | 20)'))
        self.assertEqual(Pair(1, Pair(2, 3)), isheval('(list 1 2 | 3)'))
        self.assertEqual(Pair(10, 20), isheval('(list (add 5 5) | (add 10 10))'))
        self.assertRaises(Exception, isheval, '(list | 1)')
        self.assertRaises(Exception, isheval, '(list | [4 5 6])')
    def test_eval_literals(self):
        self.assertEqual(10, isheval('10'))
    def test_eval_functions(self):
        self.assertEqual(20, isheval('((fn x 20))'))
        self.assertEqual(5, isheval('((fn x x) | 5)'))
        self.assertEqual(5, isheval('((fn x (car x)) | [5])'))
        self.assertEqual(5, isheval('((fn x (car x)) 5)'))
        self.assertEqual(Pair(5, nil), isheval('((fn x x) (add 2 3))'))
        self.assertEqual(30, isheval('((fn x (add 10 (car x))) 20)'))
        self.assertRaises(Exception, isheval, '((add 1 2))')
    def test_empty_functions_return_void(self):
        self.assertEqual(void, isheval('((fn x))'))
    def test_functions_bind_hyphen(self):
        self.assertEqual(12, isheval('((fn [x] (add 3 4) (add x -)) 5)'))
        self.assertEqual(void, isheval('((fn [x] -) 5)'))
    def test_eval_functions_in_scope(self):
        my_id = isheval('(fn x x)')
        scope = Scope({'my_id': my_id}, root)
        self.assertEqual(my_id, isheval('my_id', scope))
        self.assertEqual(my_id, isheval('(my_id | (my_id | my_id))', scope))
        self.assertEqual(3, isheval('(my_id | 3)', scope))
        self.assertEqual(Pair(my_id, nil), isheval('(my_id my_id)', scope))
        self.assertEqual(my_id, isheval('(my_id | my_id)', scope))
        self.assertEqual(Pair(20, nil), isheval('(my_id 20)', scope))
    def test_eval_nested_functions(self):
        compose = isheval('(fn x (fn y ((car (cdr x)) ((car x) (car y)))))')
        self.assertEqual(Function, type(compose))
        scope = Scope({'compose': compose}, root)
        self.assertEqual(compose, isheval('compose', scope))
        self.assertEqual(10, isheval('((compose id id) 10)', scope))
        self.assertEqual(Pair(10, nil), isheval('((compose id id) [10])', scope))
    def test_function_patterns_simple(self):
        compose = isheval('(fn [fn1 fn2] (fn [y] (fn2 (fn1 y))))')
        scope = Scope({'compose': compose}, root)
        self.assertEqual(10, isheval('((compose id id) 10)', scope))

        my_car = isheval('(fn [x:xs] x)')
        scope = Scope({'my-car': my_car}, root)
        self.assertEqual(3, isheval('(my-car [3 4 5])', scope))

        my_id = isheval('(fn x x)')
        scope = Scope({'my-id': my_id}, root)
        self.assertEqual(20, isheval('(my-id | 20)', scope))

        first_arg = isheval('(fn x:xs x)')
        scope = Scope({'first-arg': first_arg}, root)
        self.assertEqual(6, isheval('(first-arg 6 7 8)', scope))
    def test_function_patterns(self):
        unary_compose = isheval('''
            (fn [fn1 fn2]
                (fn [arg]
                    (fn1 (fn2 arg))
                )
            )''')
        self.assertEqual(Function, type(unary_compose))
        scope = Scope({'unary_compose': unary_compose}, root)
        cadr = isheval('(unary_compose car cdr)', scope)
        scope.set('cadr', cadr)
        self.assertEqual(2, isheval('(cadr [1 2 3])', scope))
        self.assertEqual(3, isheval('((unary_compose cadr cdr) [1 2 3])', scope))
    def test_function_shorthand(self):
        self.assertEqual(25, isheval('(#(add - 20) 5)'))
        self.assertEqual(15, isheval('(#(add -1 -2) 5 10)'))
        self.assertEqual(void, isheval('(#(id -))'))
        self.assertRaises(Exception, isheval, '(#(add -1 -2) 5)')
    def test_eval_builtins(self):
        self.assertEqual(1, isheval('(car [1])'))
        self.assertEqual(1, isheval('(car (id [1]))'))
        self.assertEqual(nil, isheval('(cdr [1])'))
        self.assertEqual(Pair(1, 2), isheval('(call cons 1 2)'))
        self.assertEqual(Pair(1, 2), isheval('(apply cons (list 1 2))'))
        self.assertEqual(Pair(1, 2), isheval('(apply cons [1 2])'))
        self.assertEqual(1, isheval('(apply car [[1 2]])'))
        self.assertEqual(Pair(1, Pair(2, nil)), isheval('((curry list 1) 2)'))

    def test_builtin_match(self):
        self.assertEqual(True, isheval('(match? (pattern x) 10)'))

    def test_curry_only_evaluates_arguments_once(self):
        count = 0
        def increment_count(args, scope):
            nonlocal count
            count += 1
            return 5
        scope = Scope({'inc': increment_count}, root)
        self.assertEqual(0, count)
        curried = isheval('(curry list (inc))', scope)
        self.assertEqual(1, count)
        scope.set('curried', curried)
        self.assertEqual(Pair(5, Pair(10, Pair(20, nil))), isheval('(curried 10 20)', scope))
        self.assertEqual(1, count)

    # lex tests

    def test_lex_bare_literals(self):
        self.assertEqual(['a'], lex('a'))
        self.assertEqual(['10'], lex('10'))

    def test_lex_forms(self):
        self.assertEqual(['(', 'a', ')'], lex('(a)'))
        self.assertEqual(['(', 'a', 'b', ')'], lex('(a b)'))
        self.assertEqual(['(', 'a', ')', 'b', ')'], lex('(a) b)'))

    def test_lex_operators(self):
        self.assertEqual(['a', ':', 'b'], lex('a:b'))
        self.assertEqual(['a', '.', 'b', ':', 'c'], lex('a.b:c'))
        self.assertEqual(['a', ':', ':', 'b'], lex('a: :b'))
        self.assertEqual(['a', '::', 'b'], lex('a::b'))

    # read tests

    def test_expand_unary_operators(self):
        self.assertEqual(
            [IdentifierNode('a'), Forms(ValueNode('_id', specials.id), IdentifierNode('b'))],
            expand_unary_operators([IdentifierNode('a'), UNARY_OPERATORS['~'], IdentifierNode('b')]))
        self.assertEqual(
            [IdentifierNode('a'), Forms(ValueNode('_id', specials.id), Forms(ValueNode('_id', specials.id), IdentifierNode('b')))],
            expand_unary_operators([IdentifierNode('a'), UNARY_OPERATORS['~'], UNARY_OPERATORS['~'], IdentifierNode('b')]))
        self.assertEqual(
            [IdentifierNode('a'), Forms(ValueNode('_get', specials.get), IdentifierNode('this'), IdentifierNode('b'))],
            expand_unary_operators([IdentifierNode('a'), UNARY_OPERATORS['@'], IdentifierNode('b')]))
    def test_expand_binary_operators(self):
        self.assertEqual(
            [Forms(ValueNode('_cons', specials.cons), IdentifierNode('a'), IdentifierNode('b'))], # TODO: FIX. Honestly, I have no idea what I wantd to fix here. This looks right to me.
            expand_binary_operators([IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b')]))
        self.assertEqual(
            [IdentifierNode('x'), Forms(ValueNode('_cons', specials.cons), IdentifierNode('a'), IdentifierNode('b')), IdentifierNode('y')],
            expand_binary_operators([IdentifierNode('x'), IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b'), IdentifierNode('y')]))
        self.assertEqual(
            [Forms(ValueNode('_cons', specials.cons), IdentifierNode('a'), Forms(ValueNode('_cons', specials.cons), IdentifierNode('b'), IdentifierNode('c')))],
            expand_binary_operators([IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b'), BINARY_OPERATORS[':'], IdentifierNode('c')]))
    def test_expand_binary_operators_precedence_and_associativity(self):
        specials_dict = {
            'get': specials.get,
            'cons': specials.cons,
            'list': specials.list_,
            'pattern-with-predicate': specials.pattern_with_predicate,
            'pattern-with-default': specials.pattern_with_default,
        }
        def special(name, *nodes):
            return Forms(ValueNode('_%s' % name, specials_dict[name]), *nodes)

        self.assertEqual(
            special('cons', special('get', IdentifierNode('a'), IdentifierNode('b')), special('cons',
                special('get', special('get', IdentifierNode('c'), IdentifierNode('d')), IdentifierNode('e')),
                IdentifierNode('f')
                )),
            read_one('a.b:c.d.e:f'))
        self.assertEqual(
            special('pattern-with-predicate',
                special('cons', IdentifierNode('a'), IdentifierNode('b')),
                IdentifierNode('even?')),
            read_one('a:b::even?'))
        self.assertEqual(
            special('pattern-with-default',
                special('pattern-with-predicate',
                    special('cons', IdentifierNode('a'), IdentifierNode('b')),
                    IdentifierNode('even?')),
                IdentifierNode('c')),
            read_one('a:b::even? = c'))
        self.assertEqual(
            special('pattern-with-default',
                special('pattern-with-predicate',
                    special('pattern-with-predicate',
                        special('cons', IdentifierNode('a'), IdentifierNode('b')),
                        IdentifierNode('even?')),
                    IdentifierNode('odd?')),
                IdentifierNode('c')),
            read_one('a:b::even?::odd? = c'))

        self.assertEqual(
            Forms(ValueNode('_list', specials.list_),
                IdentifierNode('a'),
                special('pattern-with-default',
                    IdentifierNode('b'),
                    IdentifierNode('c'))),
            read_one('[a b = c]'))
    def test_read_operator(self):
        self.assertEqual(
            Forms(ValueNode('_cons', specials.cons), IdentifierNode('a'), IdentifierNode('b')),
            read_one('a:b'))
        self.assertEqual(
            Forms(IdentifierNode('print'), Forms(ValueNode('_cons', specials.cons), IdentifierNode('a'), IdentifierNode('b'))),
            read_one('(print a:b)'))
    def test_read_bare_literals(self):
        self.assertEqual(IdentifierNode('a'), read_one('a'))
        self.assertEqual(NumericLiteralNode('10'), read_one('10'))
    def test_read_trivial_form(self):
        self.assertEqual(
            FormNode(IdentifierNode('a'), nil),
            read_one('(a)'))
    def test_read_form_with_cdr(self):
        self.assertEqual(
            FormNode(IdentifierNode('a'), IdentifierNode('b')),
            read_one('(a | b)'))
    def test_read_form_with_form_as_cdr(self):
        self.assertEqual(
            FormNode(IdentifierNode('a'), FormNode(IdentifierNode('b'), nil)),
            read_one('(a | (b))'))
    def test_read_form_without_cdr(self):
        self.assertEqual(
            Forms(IdentifierNode('a'), IdentifierNode('b')),
            read_one('(a b)'))
    def test_read_form_without_cdr_implicit_nil(self):
        self.assertEqual(
            Forms(IdentifierNode('a'), IdentifierNode('b'), PAIR_CDR_TOKEN, nil),
            read_one('(a b)'))
    def test_read_square_brackets_converts_to_list_special_form(self):
        self.assertEqual(
            Forms(ValueNode('_list', specials.list_), IdentifierNode('a'), IdentifierNode('b')),
            read_one('[a b]'))
    def test_read_square_brackets_with_cdr_converts_to_list_special_form(self):
        self.assertEqual(
            FormNode(ValueNode('_list', specials.list_), Pair(IdentifierNode('a'), IdentifierNode('b'))),
            read_one('[a | b]'))
    def test_read_square_brackets_must_have_cdr(self):
        self.assertRaises(Exception, lambda: read('[a |]'))
    def test_read_square_brackets_must_have_car(self):
        self.assertRaises(Exception, lambda: read('[| a]'))
    def test_read_square_brackets_must_have_car_and_cdr(self):
        self.assertRaises(Exception, lambda: read('[|]'))
    def test_read_square_brackets_must_not_have_multiple_cdrs(self):
        self.assertRaises(Exception, lambda: read('[a | b c]'))
    def test_read_misc(self):
        self.assertEqual(
            FormNode(IdentifierNode('id'), Pair(NumericLiteralNode('1'), nil)),
            read_one('(id 1)'))
        self.assertEqual(
            FormNode(IdentifierNode('id'), Pair(NumericLiteralNode('1'), Pair(NumericLiteralNode('2'), nil))),
            read_one('(id 1 2)'))
        self.assertEqual(
            Forms(IdentifierNode('id'), NumericLiteralNode('1')),
            read_one('(id 1)'))
        self.assertEqual(
            Forms(IdentifierNode('id'), FormNode(IdentifierNode('add'),
                Pair(NumericLiteralNode('1'), Pair(NumericLiteralNode('2'), nil)))),
            read_one('(id (add 1 2))'))
        self.assertEqual(
            Forms(IdentifierNode('id'), FormNode(ValueNode('_list', specials.list_),
                Pair(NumericLiteralNode('1'), Pair(NumericLiteralNode('2'), nil)))),
            read_one('(id [1 2])'))
        self.assertEqual(
            Forms(IdentifierNode('id'), FormNode(ValueNode('_list', specials.list_),
                Pair(NumericLiteralNode('1'), NumericLiteralNode('2')))),
            read_one('(id [1 | 2])'))
        self.assertEqual(
            Forms(Forms(IdentifierNode('id'), IdentifierNode('id')), NumericLiteralNode('1')),
            read_one('((id id) 1)'))

        self.assertEqual(Forms(IdentifierNode('print'),
            Forms(IdentifierNode('add'),
                NumericLiteralNode('5'),
                NumericLiteralNode('6'))),
            read_one('(print (add 5 6))'))

        self.assertEqual(
            Forms(IdentifierNode('print'),
                FormNode(ValueNode('_list', specials.list_), Pair(NumericLiteralNode('7'), NumericLiteralNode('8')))),
            read_one('(print [7 | 8])'))

        self.assertEqual(
            Forms(
                IdentifierNode('print'),
                Forms(
                    ValueNode('_list', specials.list_),
                    Forms(
                        IdentifierNode('add'),
                        NumericLiteralNode('10'),
                        NumericLiteralNode('20')
                    )
                ),
            ),
            read_one('(print [(add 10 20)])'))

    # pattern tests

    def test_pattern_allows_empty_square_brackets_as_nil(self):
        self._test_pattern('(pattern [])', 'nil', {})

    def test_identifier_pattern_match(self):
        self._test_pattern('(pattern a)', '10', {'a': 10})
        self._test_pattern('(pattern a)', 'nil', {'a': nil})
        self._test_pattern('(pattern a)', '[1 2 3]', {'a': Pair(1, Pair(2, Pair(3, nil)))})
    def test_value_pattern_match(self):
        self._test_pattern('(pattern 10)', '10', {})
        self._test_pattern_fails('(pattern 10)', 'nil')
        self._test_pattern_fails('(pattern 10)', '11')
        self._test_pattern_fails('(pattern 10)', '[1 2 3]')

        self._test_pattern('(pattern a:10)', '20:10', {'a': 20})
        self._test_pattern_fails('(pattern a:10)', '11:12')
        self._test_pattern_fails('(pattern a:10)', '5')
        self._test_pattern_fails('(pattern a:10)', 'nil')

        self._test_pattern('(pattern [a 5 b])', '[3 5 7]', {'a': 3, 'b': 7})
        self._test_pattern_fails('(pattern [a 5 b])', '[10 11 12]')
        self._test_pattern_fails('(pattern [a 5 b])', 'nil')

        self._test_pattern('(pattern [])', 'nil', {})
        self._test_pattern_fails('(pattern [])', '1')
        self._test_pattern_fails('(pattern [])', '1:2')
        self._test_pattern_fails('(pattern [])', '[1 2]')
        self._test_pattern_fails('(pattern [])', 'nil:nil')

    def test_predicated_patterns(self):
        self.assertTrue(
            isheval('(pattern-with-predicate (pattern x) even?)') ==
            isheval('(pattern (pattern-with-predicate (pattern x) even?))') ==
            isheval('(pattern x)::even?') ==
            isheval('(pattern-with-predicate x even?)') ==
            isheval('(pattern x::even?)')
        )
        self._test_pattern('(pattern x::even?)', '10', {'x': 10})
        self._test_pattern_fails('(pattern x::even?)', '11')

    def test_defaulted_patterns(self):
        self._test_pattern('(pattern [a | b])', '1:2', {'a': 1, 'b': 2})
        self._test_pattern('(pattern [a | b])', '[1]', {'a': 1, 'b': nil})
        self._test_pattern('(pattern [a | b])', '1:2:3', {'a': 1, 'b': Pair(2, 3)})
        self._test_pattern_fails('(pattern [a | b])', 'nil')

        # This is a somewhat useless pattern -- the default can never be triggered,
        # since you can never have a cons cell without a cdr (although nil can be
        # thought of as a cons cell without a car).
        self._test_pattern('(pattern [a | b = 20])', '1:2', {'a': 1, 'b': 2})
        self._test_pattern_fails('(pattern [a | b = 20])', '1')
        self._test_pattern_fails('(pattern [a | b = 20])', 'nil')

        self._test_pattern('(pattern [a = 10 | b])', '1:2', {'a': 1, 'b': 2})
        # THIS IS COUNTER-INTUITIVE.
        # At least, it's not what I expected when I first wrote these tests.
        # To explain why it works, though, think of it as nothing:nil -- nothing cons nil is
        # just nil -- you didn't cons anything onto it, so it didn't change. And you can
        # match nothing:nil -- nothing goes to (pattern a = 10), which can accept nothing
        # and simply returns its default value. Then nil goes to b. And it works.
        self._test_pattern('(pattern [a = 10 | b])', 'nil', {'a': 10, 'b': nil})
        self._test_pattern_fails('(pattern [a = 10 | b])', '1')

        self._test_pattern('(pattern [a = 10 | b = 20])', '1:2', {'a': 1, 'b': 2})
        # This is equivalent to nothing:nil, as explained above.
        self._test_pattern('(pattern [a = 10 | b = 20])', 'nil', {'a': 10, 'b': nil})
        self._test_pattern_fails('(pattern [a = 10 | b = 20])', '1')

        self._test_pattern('(pattern [a = 10 | b = 20]:c)', '[1 | 2]:3', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern [a = 10 | b = 20]:c)', 'nil', {'a': 10, 'b': 20, 'c': nil})

        self._test_pattern('(pattern [a b]:c)', '[1 2]:nil', {'a': 1, 'b': 2, 'c': nil})
        self._test_pattern_fails('(pattern [a = 10 b = 20]:c)', 'nil')
        # This is a little weird when you think of it as a list, but if you think of it as a ConsPattern
        # whose cdr_pattern is a ConsPattern then this does make sense.
        self._test_pattern('(pattern [a = 10 b = 20 | c = 30]:d)', 'nil', {'a': 10, 'b': 20, 'c': 30, 'd': nil})
        self._test_pattern('(pattern [a b]:c)', '[1 2]:nil', {'a': 1, 'b': 2, 'c': nil})

        self._test_pattern('(pattern [[a | b] | c])', '[1|2]:3', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern_fails('(pattern [[a | b] | c])', '[1|2]')
        self._test_pattern_fails('(pattern [[a | b] | c])', '[1]')
        self._test_pattern_fails('(pattern [[a | b] | c])', 'nil')

        self._test_pattern('(pattern [[a | b] c])', '[1:2 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern_fails('(pattern [[a | b] c])', '[1|2]')
        self._test_pattern_fails('(pattern [[a | b] c])', '[1 3]')
        self._test_pattern_fails('(pattern [[a | b] c])', '[1]')
        self._test_pattern_fails('(pattern [[a | b] c])', 'nil')

        self._test_pattern('(pattern a::even? = 10)', '7', {'a': 10})
        self._test_pattern('(pattern a::even? = 10)', '8', {'a': 8})

        self._test_pattern('(pattern [a b = 20])', '[1 2]', {'a': 1, 'b': 2})
        self._test_pattern('(pattern [a b = 20])', '[1]', {'a': 1, 'b': 20})
        self._test_pattern('(pattern [a b = 20])', '1:2:nil', {'a': 1, 'b': 2})
        self._test_pattern_fails('(pattern [a b = 20])', '1:2:3')
        self._test_pattern_fails('(pattern [a b = 20])', 'nil')

        self._test_pattern('(pattern [a b c = 30])', '[1 2 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern [a b c = 30])', '[1 2]', {'a': 1, 'b': 2, 'c': 30})
        self._test_pattern_fails('(pattern [a b c = 30])', '[1]')
        self._test_pattern_fails('(pattern [a b c = 30])', 'nil')

        self._test_pattern('(pattern [a b = 20 c = 30])', '[1 2 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern [a b = 20 c = 30])', '[1 2]', {'a': 1, 'b': 2, 'c': 30})
        self._test_pattern('(pattern [a b = 20 c = 30])', '[1]', {'a': 1, 'b': 20, 'c': 30})
        self._test_pattern_fails('(pattern [a b = 20 c = 30])', 'nil')

        self._test_pattern('(pattern [a = 10 b = 20 c = 30])', '[1 2 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern [a = 10 b = 20 c = 30])', '[1 2]', {'a': 1, 'b': 2, 'c': 30})
        self._test_pattern('(pattern [a = 10 b = 20 c = 30])', '[1]', {'a': 1, 'b': 20, 'c': 30})
        self._test_pattern('(pattern [a = 10 b = 20 c = 30])', 'nil', {'a': 10, 'b': 20, 'c': 30})
        self._test_pattern_fails('(pattern [a = 10 b = 20 c = 30])', '1')

        self._test_pattern('(pattern [a b = 20 []:[]])', '[1 2 nil:nil]', {'a': 1, 'b': 2})
        self._test_pattern_fails('(pattern [a b = 20 []:[]])', '[1]')
        self._test_pattern_fails('(pattern [a b = 20 []:[]])', '[1 2 nil]')

        self._test_pattern('(pattern [a b = 20 | []:[]])', '[1 2 | nil:nil]', {'a': 1, 'b': 2})
        self._test_pattern('(pattern [a b = 20 | []:[]])', '[1 2 nil]', {'a': 1, 'b': 2})
        self._test_pattern_fails('(pattern [a b = 20 | []:[]])', '[1]')
        self._test_pattern_fails('(pattern [a b = 20 | []:[]])', '[1 nil]')

        self._test_pattern('(pattern [a b = 20 c])', '[1 2 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern [a b = 20 c])', '[1 2 nil]', {'a': 1, 'b': 2, 'c': nil})
        self._test_pattern_fails('(pattern [a b = 20 c])', '[1 2]')
        self._test_pattern_fails('(pattern [a b = 20 c])', '[1]')
        self._test_pattern_fails('(pattern [a b = 20 c])', 'nil')

        self._test_pattern('(pattern [a b = 20 | c = 30])', '[1 2 | 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern [a b = 20 | c = 30])', '[1 2]', {'a': 1, 'b': 2, 'c': nil})
        self._test_pattern('(pattern [a b = 20 | c = 30])', '[1]', {'a': 1, 'b': 20, 'c': nil}) # counter-intuitive!
        self._test_pattern_fails('(pattern [a b = 20 | c = 30])', 'nil')

        self._test_pattern('(pattern [a b = 20 | c])', '[1 2 | 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern [a b = 20 | c])', '[1 2]', {'a': 1, 'b': 2, 'c': nil})
        self._test_pattern('(pattern [a b = 20 | c])', '[1]', {'a': 1, 'b': 20, 'c': nil}) # counter-intuitive!
        self._test_pattern_fails('(pattern [a b = 20 | c])', 'nil')

        self._test_pattern('(pattern [a b = 20 3])', '[1 2 3]', {'a': 1, 'b': 2})
        self._test_pattern_fails('(pattern [a b = 20 3])', '[1 2]')
        self._test_pattern_fails('(pattern [a b = 20 3])', '[1 3]')
        self._test_pattern_fails('(pattern [a b = 20 3])', '[1]')
        self._test_pattern_fails('(pattern [a b = 20 3])', 'nil')

        self._test_pattern('(pattern [a b = 20 | 3])', '[1 2 | 3]', {'a': 1, 'b': 2})
        self._test_pattern_fails('(pattern [a b = 20 | 3])', '[1 2]')
        self._test_pattern_fails('(pattern [a b = 20 | 3])', '[1 3]')
        self._test_pattern_fails('(pattern [a b = 20 | 3])', '[1 | 2]')
        self._test_pattern_fails('(pattern [a b = 20 | 3])', '[1 | 3]')
        self._test_pattern_fails('(pattern [a b = 20 | 3])', '[1]')
        self._test_pattern_fails('(pattern [a b = 20 | 3])', 'nil')

        self._test_pattern('(pattern [a b = 20 []])', '[1 2 nil]', {'a': 1, 'b': 2})
        self._test_pattern('(pattern [a b = 20 []])', '[1 nil nil]', {'a': 1, 'b': nil})
        self._test_pattern_fails('(pattern [a b = 20 []])', '[1 nil]')
        self._test_pattern_fails('(pattern [a b = 20 []])', '[1]')
        self._test_pattern_fails('(pattern [a b = 20 []])', 'nil')

        self._test_pattern('(pattern [a b = 20 | []])', '[1 2]', {'a': 1, 'b': 2})
        self._test_pattern('(pattern [a b = 20 | []])', '[1]', {'a': 1, 'b': 20})
        self._test_pattern_fails('(pattern [a b = 20 | []])', '[1 2 nil]')

    def test_cons_pattern_match_list(self):
        self._test_pattern('(pattern [a b | c])', '[1 2 | 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern [a b | c])', '[1 2]', {'a': 1, 'b': 2, 'c': nil})
        self._test_pattern_fails('(pattern [a b | c])', '[1]')
        self._test_pattern_fails('(pattern [a b | c])', 'nil')

        self._test_pattern('(pattern [a b c])', '[1 2 3]', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern_fails('(pattern [a b c])', '[1 2 | 3]')
        self._test_pattern_fails('(pattern [a b c])', '[1 2]')
        self._test_pattern_fails('(pattern [a b c])', '[1]')
        self._test_pattern_fails('(pattern [a b c])', 'nil')

        self._test_pattern('(pattern []:[])', 'nil:nil', {})
        self._test_pattern_fails('(pattern []:[])', 'nil')

        self._test_pattern('(pattern []:[]:[]:[])', 'nil:nil:nil:nil', {})
        self._test_pattern_fails('(pattern []:[]:[]:[])', 'nil')

        self._test_pattern('(pattern []:a)', 'nil:1', {'a': 1})
        self._test_pattern_fails('(pattern []:a)', 'nil')

        self._test_pattern('(pattern a:b)', '1:2', {'a': 1, 'b': 2})
        self._test_pattern('(pattern a:b)', '[1 | 2]', {'a': 1, 'b': 2})
        self._test_pattern('(pattern a:b)', '[1 2 3]', {'a': 1, 'b': Pair(2, Pair(3, nil))})
        self._test_pattern_fails('(pattern a:b)', 'nil')

        self._test_pattern('(pattern a:b:c)', '1:2:3', {'a': 1, 'b': 2, 'c': 3})
        self._test_pattern('(pattern a:b:c)', '[1 2 3]', {'a': 1, 'b': 2, 'c': Pair(3, nil)})
        self._test_pattern_fails('(pattern a:b:c)', '1:2')
        self._test_pattern_fails('(pattern a:b:c)', 'nil')

    def test_calling_pattern(self):
        self.assertEqual(5, isheval('((pattern a) 5) a'))
        self.assertEqual(10, isheval('(a = 10) a'))
        self.assertRaises(Exception, isheval, '((pattern 5) 10)')
        self.assertEqual(15, isheval('''
            (foo = 10)
            (change-foo = (fn -
                (foo = 15)))
            (change-foo)
            foo
            '''))

    def test_aliased_pattern(self):
        self.assertEqual(10, isheval('((pattern a/b) 5) (add a b)'))
        self.assertEqual(15, isheval('((pattern a/b/c) 5) (add (add a b) c)'))
        self.assertRaises(Exception, isheval, '((pattern a/b::even?) 5) b')
        self.assertEqual(12, isheval('((pattern a/b::even?) 6) (add a b)'))

    def test_evaluation_within_patterns(self):
        self.assertEqual(10, isheval('((pattern [foo (add 3 2)]) [10 5]) foo'))
        self.assertRaises(Exception, isheval, '((pattern (add 3 2)) 6)')

    # callable tests

    def test_pairs_are_callable(self):
        self.assertEqual(2, isheval('(car:cdr [1 2 3])'))
    def test_pairs_are_callable_with_user_defined_functions(self):
        self.assertEqual(3, isheval('(inc = (fn [a] (add a 1))) (inc:car:cdr [1 2 3])'))

    # object tests

    def test_objects_basic(self):
        self.assertEqual(10, isheval('(get (object foo:10) foo)'))
    def test_objects_set(self):
        self.assertEqual(10, isheval('(obj = (object)) (set obj foo 10) (get obj foo)'))
    def test_objects_special_syntax(self):
        self.assertEqual(10, isheval('(get {foo: 10} foo)'))
    def test_objects_get_syntax(self):
        self.assertEqual(10, isheval('{foo: 10}.foo'))
    def test_get_in_object_is_evaluated_once(self):
        self.assertEqual(1, isheval('''
            (a = 0)
            (obj = {baz: 10})
            (side-effect-get = (fn - (a = (add a 1)) get))
            { ((side-effect-get) obj baz) }
            a'''))
    def test_objects_identifier_shorthand(self):
        self.assertEqual(10, isheval('''
            (foo = 10)
            (get {foo} foo)
            '''))
    def test_objects_get_shorthand(self):
        self.assertEqual(10, isheval('''
            (obj = {foo: {bar: 10}})
            (get {obj.foo.bar} bar)
            '''))

    # dictionary tests

    def test_dictionaries_basic(self):
        self.assertEqual(10, isheval('(get (dictionary 5:10) 5)'))
    def test_dictionaries_set(self):
        self.assertEqual(10, isheval('(dict = (dictionary)) (set dict 5 10) (get dict 5)'))
    def test_dictionaries_special_syntax(self):
        self.assertEqual(10, isheval('(get #{5: 10} 5)'))
    def test_dictionaries_get_syntax(self):
        self.assertEqual(10, isheval('#{5: 10}.5'))
    def test_dictionaries_dont_treat_identifiers_specially(self):
        self.assertEqual(10, isheval('''
            (foo = 5)
            #{foo: 10}.5'''))
    def test_dictionaries_can_still_have_attributes(self):
        self.assertEqual(Pair(10, Pair(20, 30)), isheval('''
            (dict = (dictionary))
            (set dict 5 10)
            (set dict foo 20)
            (set dict #foo 30)
            dict.5 : dict.foo : dict.#foo'''))

    # test methods

    def test_binding_methods(self):
        self.assertEqual(15, isheval('''
            (meth = (md [a] (add a @bar)))
            (foo = {bar: 10})
            ((bind meth foo) 5)'''))
    def test_get_binds_methods(self):
        self.assertEqual(15, isheval('''
            (obj = { baz: 5, meth: (md [a] (add a @baz)) })
            (obj.meth 10)'''))
    def test_cant_invoke_unbound_method(self):
        self.assertRaises(Exception, isheval, '((md - 10) 5)')

    # test promises

    def test_promises(self):
        self.assertEqual(Pair(0, Pair(0, Pair(1, 1))), isheval('''
            (x = 0)
            (side-effect = (fn -
                (x = (add x 1))
                20))

            (a = x)
            (def y (delay (side-effect)))
            (b = x)
            (force y)
            (c = x)
            (force y)
            (d = x)
            a:b:c:d'''))
    def test_pairs_force_cdrs(self):
        self.assertEqual(Pair(0, Pair(0, Pair(1, 1))), isheval('''
            (x = 0)
            (side-effect = (fn -
                (x = (add x 1))
                20))

            (a = x)
            (pair = 10:(delay (side-effect)))
            pair.cdr-slot
            (b = x)
            pair.cdr
            (c = x)
            (force pair.cdr-slot)
            (d = x)
            a:b:c:d'''))

    # test multifunctions

    def test_multi_functions(self):
        self.assertEqual(Pair(11, 30), isheval('''
        (def multi-test (mfn
            ([a] (add a 1))
            ([a b] (add a b))
        ))
        (multi-test 10):(multi-test 10 20)'''))

unittest.main()
