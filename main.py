from evaluator import isheval
from reader import read, lex

code = '''
(id | 1)
(id | (add 1 2))
(id 1)
(print ((fn x (add (car x) 1)) 5))
'''

print(isheval(code))
