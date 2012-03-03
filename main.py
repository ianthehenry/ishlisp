from evaluator import isheval
from reader import read, lex

code = '''
(print (cons 1 2))
(print 1:2)
'''

print(isheval(code))
print(repr(read('(print 1 2:3:4)')[0]))
print(repr(read('(print (cons 1 2):3 2:3:4:nil)')[0]))
