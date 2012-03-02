from evaluator import isheval

code = '''
(print (add 5 6))
(print (add 5 (add 1 2)))
'''
# (print [7 | 8])
# (print [(add 10 20)])

isheval(code)
