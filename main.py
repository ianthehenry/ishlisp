import re

nil = None
class Nil:
    def __init__(self):
        global nil
        assert nil is None

    def __repr__(self):
        return 'nil'
nil = Nil()

def tuplify(lst):
    if len(lst) == 0:
        return nil
    if type(lst) is not list:
        return lst
    return (tuplify(lst[0]), tuplify(lst[1:]))

def lex(code): # converts string to tokens, currently represented as simple strings
    boundaries = set([' ', '\t', '\n', ')', '(', '|', '[', ']', '{', '}'])
    tokens = []
    def end_token(char_list):
        token = ''.join(char_list)
        if not re.match(r'^\s*$', token):
            tokens.append(token)
    current_token = []
    for c in code:
        if c in boundaries:
            end_token(current_token)
            end_token([c])
            current_token = []
        else:
            current_token += c
    return tokens

def split(lst, predicate):
    first = []
    second = []
    i = 0
    while i < len(lst):
        item = lst[i]
        i += 1
        if predicate(item):
            break
        else:
            first.append(item)
    else:
        raise Exception('Invalid split: predicate never resolved to true')
    while i < len(lst):
        second.append(lst[i])
        i += 1
    return (first, second)

class FormToken:
    def __init__(self, sexp):
        if type(sexp) is list:
            self.sexp = tuplify(sexp)
        else:
            self.sexp = sexp
        self.car = sexp[0]
        self.cdr = sexp[1]
    def __repr__(self):
        return 'F' + repr(self.sexp)
    def __len__(self):
        return len(self.sexp)
    def __eq__(self, other):
        return type(other) is FormToken and self.sexp == other.sexp

class PairToken:
    def __init__(self, sexp):
        if type(sexp) is list:
            self.sexp = tuplify(sexp)
        else:
            self.sexp = sexp
        self.car = sexp[0]
        self.cdr = sexp[1]
    def __repr__(self):
        return 'P' + repr(self.sexp)
    def __len__(self):
        return len(self.sexp)
    def __eq__(self, other):
        return type(other) is PairToken and self.sexp == other.sexp

def read_matched_code(tokens, start, end, constructor):
    nesting_depth = 1
    def pred(token):
        nonlocal nesting_depth
        if token == start:
            nesting_depth += 1
            return False
        if token == end:
            nesting_depth -= 1
            return nesting_depth == 0

    form_tokens, remaining_tokens = split(tokens, pred)
    return (constructor((form_tokens[0], read(form_tokens[1:]))), read(remaining_tokens))

matched_tokens = {
    '(': (')', FormToken),
    '[': (']', PairToken)
}

def read(tokens): # converts token stream to s-expressions, parses numeric literals, etc
    if len(tokens) == 0:
        return nil
    if tokens[0] in matched_tokens:
        opening = tokens[0]
        return read_matched_code(tokens[1:], opening, *matched_tokens[opening])

    return (tokens[0], read(tokens[1:]))

def isheval(statement, scope):
    assert statement is not nil

    if type(statement) is FormToken:
        fn = scope.get(statement.car)
        return fn(statement.cdr, scope)
    else:
        return scope.get(statement)

code = '''
(print (add 5 6))
(print [7 | 8])
'''

actual = read(lex(code))
expected = tuplify([
    FormToken(['print', FormToken(['add', '5', '6'])]),
    FormToken(['print', PairToken(['7', '|', '8'])])
])

assert(actual == expected)

class Scope:
    def __init__(self, dict, parent):
        self.dict = dict
        self.parent = parent
    def get(self, symbol):
        if symbol in self.dict:
            return self.dict[symbol]
        if self.parent is None:
            raise Exception("symbol '%s' is not in scope" % symbol)
        return self.parent.get(symbol)

scope = Scope({
    'print': lambda arg, scope: print(isheval(arg[0], scope)),
    'add': lambda arg, scope: arg[0] + arg[1][0],
    'nil': nil
}, None)

print(actual)
isheval(actual[0], scope)
