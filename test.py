import unittest
from reader import read, parse_forms, FormNode, PAIR_CDR_TOKEN, NumericLiteralNode, IdentifierNode, nil
from evaluator import isheval, Pair

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

    def _test_builtin_id(self):
        self.assertEqual(2, isheval('(id | 2)'))
        self.assertEqual(5, isheval('(id | (add 2 3))'))
        self.assertEqual(Pair(1, nil), isheval('(id | [1]'))
        self.assertEqual(Pair(1, 2), isheval('(id | [1 | 2]'))
        self.assertEqual(Pair(1, nil), isheval('(id 1)'))
        self.assertEqual(20, isheval('((id | id) 10)'))
        # self.assertEqual(Pair(10, 20), isheval('[(add 5 5) | (add 10 10)]'))

    def _test_eval_lists(self):
        self.assertEqual(Pair(1, nil), isheval('[1]'))
        self.assertEqual(Pair(1, Pair(2, Pair(3, nil))), isheval('[1 2 3]'))
        self.assertEqual(Pair(1, 2), isheval('[1 | 2]'))
        self.assertEqual(Pair(1, Pair(2, 3)), isheval('[1 2 | 3]'))
        self.assertEqual(Pair(10, nil), isheval('[(add 5 5)]'))
        self.assertEqual(Pair(10, 20), isheval('[(add 5 5) | (add 10 10)]'))

        self.assertEqual(Pair(7, Pair(8, Pair(9, nil))), isheval('(list 7 8 9)'))
        self.assertEqual(Pair(4, Pair(5, Pair(6, nil))), isheval('(list | (4 5 6))'))
        self.assertEqual(Pair(1, Pair(2, 3)), isheval('(list 1 2 | 3)'))

        self.assertEqual(Pair(30, nil), isheval('[(add 10 20)]'))
        self.assertEqual(Pair(30, 50), isheval('[(add 10 20) | (add 25 25)]'))

    def _test_eval_fns(self):
        self.assertEqual(20, isheval('((fn x 20))'))
        self.assertEqual(5, isheval('((fn x x) | 5)'))
        self.assertEqual(5, isheval('((fn x (car x)) | [5])'))
        self.assertEqual(5, isheval('((fn x (car x)) 5)'))
        self.assertEqual(Pair(5, nil), isheval('((fn x x) (add 2 3)))'))
        self.assertEqual(30, isheval('((fn x (add 10 (car x))) 20)'))

    def _test_builtins(self):
        self.assertEqual(1, isheval('(car [1])'))
        self.assertEqual(nil, isheval('(cdr [1])'))
        self.assertEqual(nil, isheval('(id | nil)'))
        self.assertEqual(5, isheval('(id | 5)'))
        self.assertEqual(Pair(5, nil), isheval('(id | [5])'))
        self.assertEqual(5, isheval('(id | (add 2 3))'))
        self.assertEqual(Pair(5, nil), isheval('(id (add 2 3))'))

    # read tests

    def test_read_trivial_form(self):
        self.assertEqual(
            FormNode(IdentifierNode('a'), nil),
            read('(a)')[0])
    def test_read_form_with_cdr(self):
        self.assertEqual(
            FormNode(IdentifierNode('a'), IdentifierNode('b')),
            read('(a | b)')[0])
    def test_read_form_with_form_as_cdr(self):
        self.assertEqual(
            FormNode(IdentifierNode('a'), FormNode(IdentifierNode('b'), nil)),
            read('(a | (b))')[0])
    def test_read_form_without_cdr(self):
        self.assertEqual(
            Forms(IdentifierNode('a'), IdentifierNode('b')),
            read('(a b)')[0])
    def test_read_form_without_cdr_implicit_nil(self):
        self.assertEqual(
            Forms(IdentifierNode('a'), IdentifierNode('b'), PAIR_CDR_TOKEN, nil),
            read('(a b)')[0])
    def test_read_square_brackets_converts_to_list_special_form(self):
        self.assertEqual(
            Forms(IdentifierNode('list'), IdentifierNode('a'), IdentifierNode('b')),
            read('[a b]')[0])
    def test_read_square_brackets_with_cdr_converts_to_list_special_form(self):
        self.assertEqual(
            FormNode(IdentifierNode('list'), Pair(IdentifierNode('a'), IdentifierNode('b'))),
            read('[a | b]')[0])
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
