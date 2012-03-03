from evaluator import isheval
from reader import read, lex

code = '''
(print 1:2)
'''

isheval(code)

print(repr(read('(print a.b)')[0]))
print(repr(read('(print a . b)')[0]))
print(repr(read('(print a . b : c . d . e : f)')[0]))
print(repr(read('(print a.b:c.d.e:f)')[0]))
print(repr(read('[a b | c:d]')[0]))
