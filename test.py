import unittest
from reader import lex, read, parse_forms, FormNode, BINARY_OPERATORS, PAIR_CDR_TOKEN, NumericLiteralNode, IdentifierNode, nil, expand_binary_operators, ValueNode
from evaluator import isheval, Pair, root, Scope
from types import LambdaType, FunctionType
import specials

def read_one(code):
    return read(code)[0]

def Forms(*nodes):
    return parse_forms(nodes)

class Tests(unittest.TestCase):
    def _repr_is_homoiconic(self, code):
        self.assertEqual(code, repr(read_one(code)))

    # repr tests

    def test_list_repr_empty_lists_are_nil(self):
        self.assertEqual('nil', repr(read_one('[]')))
    def test_form_node_repr(self):
        self._repr_is_homoiconic('(a)')
        self._repr_is_homoiconic('(a | b)')
        self._repr_is_homoiconic('(a b | 3)')
        self._repr_is_homoiconic('(a b 3)')
        self._repr_is_homoiconic('(a (b))')
        self._repr_is_homoiconic('(a | (b))')
        # self.assertRaises(Exception, read, '()') # TODO
        self.assertRaises(Exception, read, '(|)')
        self.assertRaises(Exception, read, '(a |)')
        self.assertRaises(Exception, read, '(| a)')
        self.assertRaises(Exception, read, '(a | b 3)')

    # eval tests

    def test_eval(self):
        self.assertEqual(11, isheval('(add 5 6)'))
        self.assertEqual(8, isheval('(add 5 (add 1 2))'))
        self.assertEqual(18, isheval('(add (add 5 10) (add 1 2))'))
    def test_eval_builtin_id(self):
        self.assertEqual(2, isheval('(id | 2)'))
        self.assertEqual(5, isheval('(id | (add 2 3))'))
        self.assertEqual(Pair(1, nil), isheval('(id | (list 1)'))
        self.assertEqual(Pair(1, nil), isheval('(id | [1]'))
        self.assertEqual(Pair(1, 2), isheval('(id | [1 | 2]'))
        self.assertEqual(Pair(1, nil), isheval('(id 1)'))
        self.assertEqual(20, isheval('((id | id) | 20)'))
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
        compose = isheval('(fn x (fn y ((car (cdr x)) | ((car x) | y))))')
        self.assertEqual(LambdaType, type(compose))
        scope = Scope({'compose': compose}, root)
        self.assertEqual(compose, isheval('compose', scope))
        self.assertEqual(10, isheval('((compose id id) | 10)', scope))
        self.assertEqual(Pair(10, nil), isheval('((compose id id) 10)', scope))
    def test_function_patterns_simple(self):
        compose = isheval('(fn [fn1 fn2] (fn y (fn2 | (fn1 | y))))')
        scope = Scope({'compose': compose}, root)
        self.assertEqual(10, isheval('((compose id id) | 10)', scope))

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
        self.assertEqual(FunctionType, type(unary_compose))
        scope = Scope({'unary_compose': unary_compose}, root)
        cadr = isheval('(unary_compose car cdr)', scope)
        scope.set('cadr', cadr)
        self.assertEqual(2, isheval('(cadr [1 2 3])', scope))
        self.assertEqual(3, isheval('((unary_compose cadr cdr) [1 2 3])', scope))
    def test_eval_builtins(self):
        self.assertEqual(1, isheval('(car [1])'))
        self.assertEqual(1, isheval('(car (id 1))'))
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

    def test_expand_binary_operators(self):
        self.assertEqual(
            [Forms(ValueNode('_cons', specials.cons), IdentifierNode('a'), IdentifierNode('b'))], # TODO: FIX
            expand_binary_operators([IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b')]))
        self.assertEqual(
            [IdentifierNode('x'), Forms(ValueNode('_cons', specials.cons), IdentifierNode('a'), IdentifierNode('b')), IdentifierNode('y')],
            expand_binary_operators([IdentifierNode('x'), IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b'), IdentifierNode('y')]))
        self.assertEqual(
            [Forms(ValueNode('_cons', specials.cons), IdentifierNode('a'), Forms(ValueNode('_cons', specials.cons), IdentifierNode('b'), IdentifierNode('c')))],
            expand_binary_operators([IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b'), BINARY_OPERATORS[':'], IdentifierNode('c')]))
    def test_expand_binary_operators_precedence_and_associativity(self):
        self.assertEqual(
            Forms(ValueNode('_cons', specials.cons), Forms(
                ValueNode('_get', specials.get), IdentifierNode('a'), IdentifierNode('b')), Forms(
                ValueNode('_cons', specials.cons), Forms(
                    ValueNode('_get', specials.get), Forms(
                        ValueNode('_get', specials.get), IdentifierNode('c'), IdentifierNode('d')),
                        IdentifierNode('e')),
                IdentifierNode('f')
                )),
            read_one('a.b:c.d.e:f'))
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
            Forms(IdentifierNode('list'), IdentifierNode('a'), IdentifierNode('b')),
            read_one('[a b]'))
    def test_read_square_brackets_with_cdr_converts_to_list_special_form(self):
        self.assertEqual(
            FormNode(IdentifierNode('list'), Pair(IdentifierNode('a'), IdentifierNode('b'))),
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
            FormNode(IdentifierNode('id'), NumericLiteralNode('1')),
            read_one('(id | 1)'))
        self.assertEqual(
            FormNode(IdentifierNode('id'), FormNode(IdentifierNode('add'),
                Pair(NumericLiteralNode('1'), Pair(NumericLiteralNode('2'), nil)))),
            read_one('(id | (add 1 2)'))
        self.assertEqual(
            FormNode(IdentifierNode('id'), FormNode(IdentifierNode('list'),
                Pair(NumericLiteralNode('1'), Pair(NumericLiteralNode('2'), nil)))),
            read_one('(id | [1 2])'))
        self.assertEqual(
            FormNode(IdentifierNode('id'), FormNode(IdentifierNode('list'),
                Pair(NumericLiteralNode('1'), NumericLiteralNode('2')))),
            read_one('(id | [1 | 2])'))
        self.assertEqual(
            FormNode(FormNode(IdentifierNode('id'), IdentifierNode('id')), NumericLiteralNode('1')),
            read_one('((id | id) | 1)'))

        self.assertEqual(Forms(IdentifierNode('print'),
            Forms(IdentifierNode('add'),
                NumericLiteralNode('5'),
                NumericLiteralNode('6'))),
            read_one('(print (add 5 6))'))

        self.assertEqual(
            Forms(IdentifierNode('print'),
                FormNode(IdentifierNode('list'), Pair(NumericLiteralNode('7'), NumericLiteralNode('8')))),
            read_one('(print [7 | 8])'))

        self.assertEqual(
            Forms(
                IdentifierNode('print'),
                Forms(
                    IdentifierNode('list'),
                    Forms(
                        IdentifierNode('add'),
                        NumericLiteralNode('10'),
                        NumericLiteralNode('20')
                    )
                ),
            ),
            read_one('(print [(add 10 20)])'))

    # pattern tests

    def test_identifier_pattern_match(self):
        pattern = isheval('(pattern a)')
        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('10'), scope))
        self.assertEqual(scope.identifiers(), set(['a']))
        self.assertEqual(scope.get('a'), 10)
        self.assertTrue(pattern.match(isheval('nil'), scope))
        self.assertTrue(pattern.match(isheval('[1 2 3]'), scope))
    def test_value_pattern_match(self):
        pattern = isheval('(pattern 10)')
        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('10'), scope))
        self.assertEqual(scope.identifiers(), set([]))
        self.assertFalse(pattern.match(isheval('nil'), scope))
        self.assertFalse(pattern.match(isheval('11'), scope))
        self.assertFalse(pattern.match(isheval('[1 2 3]'), scope))

        pattern = isheval('(pattern a:10)')
        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('20:10'), scope))
        self.assertEqual(scope.identifiers(), set(['a']))
        self.assertEqual(scope.get('a'), 20)
        self.assertFalse(pattern.match(isheval('11:12'), scope))
        self.assertFalse(pattern.match(isheval('5'), scope))

        pattern = isheval('(pattern [a 5 b])')
        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('[3 5 7]'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b']))
        self.assertEqual(scope.get('a'), 3)
        self.assertEqual(scope.get('b'), 7)
        self.assertFalse(pattern.match(isheval('[10 11 12]'), scope))
        self.assertFalse(pattern.match(isheval('nil'), scope))

    def test_predicate_pattern(self):
        self.assertTrue(
            isheval('(pattern-with-predicate (pattern x) even?)') ==
            isheval('(pattern (pattern-with-predicate (pattern x) even?))') ==
            isheval('(pattern x)::even?') ==
            isheval('(pattern-with-predicate x even?)') ==
            isheval('(pattern x::even?)')
        )
        self.assertTrue(isheval('(match? (pattern x::even?) 10)'))
        self.assertFalse(isheval('(match? (pattern x::even?) 11)'))

    def test_cons_pattern_match_list(self):
        pattern = isheval('(pattern [a b | c])')
        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('[1 2 | 3]'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b', 'c']))
        self.assertEqual(scope.get('a'), 1)
        self.assertEqual(scope.get('b'), 2)
        self.assertEqual(scope.get('c'), 3)
        self.assertFalse(pattern.match(isheval('[1]'), scope))
        self.assertFalse(pattern.match(isheval('20'), scope))

        pattern = isheval('(pattern [a b c])')
        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('[4 5 6]'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b', 'c']))
        self.assertEqual(scope.get('a'), 4)
        self.assertEqual(scope.get('b'), 5)
        self.assertEqual(scope.get('c'), 6)

        pattern = isheval('(pattern a:b')
        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('[1 | 2]'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b']))
        self.assertEqual(scope.get('a'), 1)
        self.assertEqual(scope.get('b'), 2)

        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('3:4'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b']))
        self.assertEqual(scope.get('a'), 3)
        self.assertEqual(scope.get('b'), 4)

        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('[1 2 3]'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b']))
        self.assertEqual(scope.get('a'), 1)
        self.assertEqual(scope.get('b'), Pair(2, Pair(3, nil)))

        pattern = isheval('(pattern a:b:c')
        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('[5 6 | 7]'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b', 'c']))
        self.assertEqual(scope.get('a'), 5)
        self.assertEqual(scope.get('b'), 6)
        self.assertEqual(scope.get('c'), 7)

        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('8:9:10'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b', 'c']))
        self.assertEqual(scope.get('a'), 8)
        self.assertEqual(scope.get('b'), 9)
        self.assertEqual(scope.get('c'), 10)

        scope = Scope({}, None)
        self.assertTrue(pattern.match(isheval('[11 12 13 14 15]'), scope))
        self.assertEqual(scope.identifiers(), set(['a', 'b', 'c']))
        self.assertEqual(scope.get('a'), 11)
        self.assertEqual(scope.get('b'), 12)
        self.assertEqual(scope.get('c'), Pair(13, Pair(14, Pair(15, nil))))

unittest.main()
