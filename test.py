import unittest
from reader import read, FormNode, PairNode

def get_single_form(code):
    return read(code)[0]

class Tests(unittest.TestCase):
    def _repr_is_homoiconic(self, code):
        self.assertEqual(code, repr(get_single_form(code)))

    def test_pair_token_repr(self):
        self.assertEqual('nil', repr(get_single_form('[]')))
        self.assertEqual('[1 2]', repr(get_single_form('[1 | [2]]')))
        self._repr_is_homoiconic('[1]')
        self._repr_is_homoiconic('[1 | 2]')
        self._repr_is_homoiconic('[1 2 | 3]')
        self._repr_is_homoiconic('[1 2 3]')
        self.assertRaises(Exception, lambda: read('[|]'))
        self.assertRaises(Exception, lambda: read('[1 |]'))
        self.assertRaises(Exception, lambda: read('[| 1]'))
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
            FormNode('print', FormNode('add', 5, 6)),
            FormNode('print', PairNode(7, '|', 8)),
            FormNode('print', PairNode(FormNode('add', 10, 20))),
        ]
        self.assertEqual(expected, read(code))


unittest.main()
