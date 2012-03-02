import unittest
from reader import read, parse_forms, FormNode, PAIR_CDR_TOKEN, NumericLiteralNode, IdentifierNode, nil

def get_single_form(code):
    return read(code)[0]

def Forms(*nodes):
    return parse_forms(nodes)

class Tests(unittest.TestCase):
    def _repr_is_homoiconic(self, code):
        self.assertEqual(code, repr(get_single_form(code)))

    def test_list_token_repr_empty_lists_are_nil(self):
        self.assertEqual('nil', repr(get_single_form('[]')))

    def test_list_token_must_have_cdr(self):
        self.assertRaises(Exception, lambda: read('[1 |]'))

    def test_list_token_must_have_car(self):
        self.assertRaises(Exception, lambda: read('[| 1]'))

    def test_list_token_must_have_car_and_cdr(self):
        self.assertRaises(Exception, lambda: read('[|]'))

    def test_list_token_must_not_have_multiple_cdrs(self):
        self.assertRaises(Exception, lambda: read('[1 | 2 3]'))

    def test_form_token_repr(self):
        self.assertEqual('nil', repr(get_single_form('()')))
        self.assertEqual('(1 2)', repr(get_single_form('(1 | (2))')))
        self._repr_is_homoiconic('(1)')
        self._repr_is_homoiconic('(1 | 2)')
        self._repr_is_homoiconic('(1 2 | 3)')
        self._repr_is_homoiconic('(1 2 3)')
        self.assertRaises(Exception, lambda: read('(|)'))
        self.assertRaises(Exception, lambda: read('(1 |)'))
        self.assertRaises(Exception, lambda: read('(| 1)'))
        self.assertRaises(Exception, lambda: read('(1 | 2 3)'))

    def test_read_form_with_cdr(self):
        expected = Forms(IdentifierNode('a'), PAIR_CDR_TOKEN, IdentifierNode('b'))
        self.assertEqual(expected, read('(a | b)')[0])

    def test_read_form_without_cdr(self):
        expected = Forms(IdentifierNode('a'), IdentifierNode('b'))
        self.assertEqual(expected, read('(a b)')[0])

    def test_read_form_without_cdr_implicit_nil(self):
        expected = Forms(IdentifierNode('a'), IdentifierNode('b'), PAIR_CDR_TOKEN, nil)
        self.assertEqual(expected, read('(a b)')[0])

    def test_read_square_brackets_converts_to_list_special_form(self):
        expected = FormNode(IdentifierNode('list'), Forms(IdentifierNode('a'), IdentifierNode('b')))
        self.assertEqual(expected, read('[a b]')[0])

    def test_read_square_brackets_with_cdr_converts_to_list_special_form(self):
        expected = FormNode(IdentifierNode('list'), Forms(IdentifierNode('a'), PAIR_CDR_TOKEN, IdentifierNode('b')))
        self.assertEqual(expected, read('[a | b]')[0])

    def test_read(self):
        code = '''
        (print (add 5 6))
        (print [7 | 8])
        (print [(add 10 20)])
        '''

        actual = read(code)
        expected = [
            Forms(IdentifierNode('print'),
                Forms(IdentifierNode('add'),
                    NumericLiteralNode('5'),
                    NumericLiteralNode('6'))),
            Forms(IdentifierNode('print'),
                FormNode(IdentifierNode('list'), Forms(
                    NumericLiteralNode('7'),
                    PAIR_CDR_TOKEN,
                    NumericLiteralNode('8')))),
            Forms(IdentifierNode('print'),
                FormNode(IdentifierNode('list'), Forms(
                    Forms(IdentifierNode('add'),
                        NumericLiteralNode('10'),
                        NumericLiteralNode('20'))))),
        ]
        self.assertEqual(expected, read(code))


unittest.main()
