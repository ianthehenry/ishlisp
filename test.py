import unittest
from reader import read, tuplify, FormNode, PairNode, PAIR_CDR_TOKEN, NumericLiteralNode, IdentifierNode

def get_single_form(code):
    return read(code)[0]

class Tests(unittest.TestCase):
    def _repr_is_homoiconic(self, code):
        self.assertEqual(code, repr(get_single_form(code)))

    def test_pair_token_repr_empty_pairss_are_nil(self):
        self.assertEqual('nil', repr(get_single_form('[]')))

    def test_pair_token_repr_cdr_of_pair_token_prints_as_list(self):
        self.assertEqual('[1 2]', repr(get_single_form('[1 | [2]]')))

    def test_pair_token_repr_is_homoiconic(self):
        self._repr_is_homoiconic('[1]')
        self._repr_is_homoiconic('[1 | 2]')
        self._repr_is_homoiconic('[1 2 | 3]')
        self._repr_is_homoiconic('[1 2 3]')

    def test_pair_token_must_have_cdr(self):
        self.assertRaises(Exception, lambda: read('[1 |]'))

    def test_pair_token_must_have_car(self):
        self.assertRaises(Exception, lambda: read('[| 1]'))

    def test_pair_token_must_have_car_and_cdr(self):
        self.assertRaises(Exception, lambda: read('[|]'))

    def test_pair_token_must_not_have_multiple_cdrs(self):
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

    def test_read(self):
        code = '''
        (print (add 5 6))
        (print [7 | 8])
        (print [(add 10 20)])
        '''

        actual = read(code)
        expected = [
            FormNode(IdentifierNode('print'), FormNode(IdentifierNode('add'), NumericLiteralNode('5'), NumericLiteralNode('6'))),
            FormNode(IdentifierNode('print'), PairNode(NumericLiteralNode('7'), PAIR_CDR_TOKEN, NumericLiteralNode('8'))),
            FormNode(IdentifierNode('print'), PairNode(FormNode(IdentifierNode('add'), NumericLiteralNode('10'), NumericLiteralNode('20')))),
        ]
        self.assertEqual(expected, read(code))


unittest.main()
