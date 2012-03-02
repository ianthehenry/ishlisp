from evaluator import isheval

code = '''
(print ((fn x (add (car x) 1)) 5))
'''

isheval(code)
