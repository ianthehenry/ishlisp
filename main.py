from evaluator import isheval

code = '''
(print (add 5 6))
(print (add 5 (add 1 2)))
(print [1 2 3])
(print (list | (4 5 6)))
(print (list 7 8 9))
(print [7 | 8])
(print [(add 10 20)])
(print (car [1 2 3]))
(print (cdr [1 2 3]))
(print (list 1 2 | 3))
'''

isheval(code)
