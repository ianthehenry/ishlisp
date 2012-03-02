import re
from itertools import takewhile

nil = None
class Nil:
    def __init__(self):
        global nil
        assert nil is None

    def __repr__(self):
        return 'nil'
nil = Nil()

Pair = tuple

PAIR_CDR_TOKEN = '|'

def tuplify(lst):
    if type(lst) is not tuple:
        return lst
    if len(lst) == 0:
        return nil

    if lst[0] == PAIR_CDR_TOKEN: # [| b]
        raise Exception("cannot have a cdr without a car")
    if len(lst) > 1 and lst[1] == PAIR_CDR_TOKEN:
        if len(lst) == 2: # [a |]
            raise Exception("no cdr specified after explicit cdr")
        if len(lst) > 3: # [a | b c]
            raise Exception("can only specify one cdr")
        return (lst[0], lst[2])

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

def continue_repr(tup, closing_symbol):
    assert len(tup) == 2
    car, cdr = tup

    if type(cdr) is Pair:
        return "%s %s" % (repr(car), continue_repr(cdr, closing_symbol))
    elif cdr is nil:
        return "%s%s" % (repr(car), closing_symbol)
    else:
        return "%s | %s%s" % (repr(car), repr(cdr), closing_symbol)

class FormToken:
    def __init__(self, *sexp):
        self.sexp = tuplify(sexp)
        self.car = self.sexp[0]
        self.cdr = self.sexp[1]
    def __repr__(self):
        if type(self.cdr) is Pair:
            return "(%s %s" % (repr(self.car), continue_repr(self.cdr, ')'))
        elif self.cdr is nil:
            return "%s)" % self.car
        else:
            return "(%s | %s)" % (repr(self.car), repr(self.cdr))
    def __len__(self):
        return len(self.sexp)
    def __eq__(self, other):
        return type(other) is FormToken and self.sexp == other.sexp

class PairToken:
    def __init__(self, *sexp):
        self.sexp = tuplify(sexp)
        self.car = self.sexp[0]
        self.cdr = self.sexp[1]
    def __repr__(self):
        if type(self.cdr) is Pair:
            return "[%s %s" % (repr(self.car), continue_repr(self.cdr, ']'))
        elif self.cdr is nil:
            return "%s]" % self.car
        else:
            return "[%s | %s]" % (repr(self.car), repr(self.cdr))
    def __len__(self):
        return len(self.sexp)
    def __eq__(self, other):
        return type(other) is PairToken and self.sexp == other.sexp

def read_matched_code(tokens, start, end, constructor, empty_constructor):
    nesting_depth = 1
    def pred(token):
        nonlocal nesting_depth
        if token == start:
            nesting_depth += 1
        elif token == end:
            nesting_depth -= 1
            return nesting_depth > 0
        return True

    form_tokens = list(takewhile(pred, tokens))

    if len(form_tokens) == 0:
        return (empty_constructor(), 1)

    return (constructor(*read(form_tokens)), len(form_tokens) + 1) # +1 to account for the closing paren/bracket/whatever

def is_token_numeric_literal(token):
    return re.match(r'\d+', token)

def read_single_token(token):
    if re.match(r'\d+', token):
        return int(token)
    return token

matched_tokens = {
    '(': (')', FormToken, lambda: nil), # this should actually throw an exception, but i'm allowing it for now...makes sense if nil can be used as a function
    '[': (']', PairToken, lambda: nil)
}

def read(tokens): # converts token stream to s-expressions, parses numeric literals, etc
    if len(tokens) == 0:
        return []

    first = tokens[0]

    if first in matched_tokens:
        matched_token, tokens_consumed = read_matched_code(tokens[1:], first, *matched_tokens[first])
        return [matched_token] + read(tokens[1 + tokens_consumed:])

    return [read_single_token(first)] + read(tokens[1:])

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
(print [(add 10 20)])
'''

actual = read(lex(code))
expected = [
    FormToken('print', FormToken('add', 5, 6)),
    FormToken('print', PairToken(7, '|', 8)),
    FormToken('print', PairToken(FormToken('add', 10, 20))),
]

print('; '.join(map(repr, actual)))
print('; '.join(map(repr, expected)))
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
    'id': lambda arg, scope: arg[0],
    'nil': nil
}, None)

isheval(actual[0], scope)
