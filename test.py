import unittest
from reader import lex, read, parse_forms, FormNode, BINARY_OPERATORS, PAIR_CDR_TOKEN, NumericLiteralNode, IdentifierNode, nil, expand_binary_operators
from evaluator import isheval, Pair, root, Scope
from types import LambdaType, FunctionType

def read_one(code):
    return read(code)[0]

def Forms(*nodes):
    return parse_forms(nodes)

def Pairs(*nodes):
    return parse_forms(nodes, False)

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
    def test_eval_builtins(self):
        self.assertEqual(1, isheval('(car [1])'))
        self.assertEqual(nil, isheval('(cdr [1])'))

    # lex tests

    def test_lex_bare_literals(self):
        self.assertEqual(['a'], lex('a'))
        self.assertEqual(['10'], lex('10'))

    def test_lex_forms(self):
        self.assertEqual(['(', 'a', ')'], lex('(a)'))
        self.assertEqual(['(', 'a', 'b', ')'], lex('(a b)'))
        self.assertEqual(['(', 'a', ')', 'b', ')'], lex('(a) b)'))

    # read tests

    def test_expand_binary_operators(self):
        self.assertEqual(
            [Forms(IdentifierNode('cons'), IdentifierNode('a'), IdentifierNode('b'))],
            expand_binary_operators([IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b')]))
        self.assertEqual(
            [IdentifierNode('x'), Forms(IdentifierNode('cons'), IdentifierNode('a'), IdentifierNode('b')), IdentifierNode('y')],
            expand_binary_operators([IdentifierNode('x'), IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b'), IdentifierNode('y')]))
        self.assertEqual(
            [Forms(IdentifierNode('cons'), IdentifierNode('a'), Forms(IdentifierNode('cons'), IdentifierNode('b'), IdentifierNode('c')))],
            expand_binary_operators([IdentifierNode('a'), BINARY_OPERATORS[':'], IdentifierNode('b'), BINARY_OPERATORS[':'], IdentifierNode('c')]))
    def test_expand_binary_operators_precedence_and_associativity(self):
        self.assertEqual(
            read('(cons (get a b) (cons (get (get c d) e) f))'),
            read('a.b:c.d.e:f'))
    def test_read_operator(self):
        self.assertEqual(
            Forms(IdentifierNode('cons'), IdentifierNode('a'), IdentifierNode('b')),
            read_one('a:b'))
        self.assertEqual(
            Forms(IdentifierNode('print'), Forms(IdentifierNode('cons'), IdentifierNode('a'), IdentifierNode('b'))),
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

unittest.main()
