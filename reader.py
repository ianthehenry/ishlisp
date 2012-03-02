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
PAIR_CDR_TOKEN = '|'

def tuplify(lst):
    if type(lst) is not tuple:
        assert isinstance(lst, Node)
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

def continue_repr(tup, closing_symbol):
    assert len(tup) == 2
    car, cdr = tup

    if type(cdr) is tuple:
        return "%s %s" % (repr(car), continue_repr(cdr, closing_symbol))
    elif cdr is nil:
        return "%s%s" % (repr(car), closing_symbol)
    else:
        return "%s | %s%s" % (repr(car), repr(cdr), closing_symbol)

class Node:
    pass

class FormNode(Node):
    def __init__(self, *sexp):
        self.sexp = tuplify(sexp)
        self.car = self.sexp[0]
        self.cdr = self.sexp[1]
    def __repr__(self):
        # print(self)
        # print(type(self.cdr))
        if type(self.cdr) is tuple:
            return "(%s %s" % (repr(self.car), continue_repr(self.cdr, ')'))
        elif type(self.cdr) is FormNode:
            return "(%s %s" % (repr(self.car), continue_repr(self.cdr.sexp, ')'))
        elif self.cdr is nil:
            return "(%s)" % self.car
        else:
            return "(%s | %s)" % (repr(self.car), repr(self.cdr))
    def __len__(self):
        return len(self.sexp)
    def __eq__(self, other):
        return type(other) is FormNode and self.sexp == other.sexp

class PairNode(Node):
    def __init__(self, *sexp):
        self.sexp = tuplify(sexp)
        self.car = self.sexp[0]
        self.cdr = self.sexp[1]
    def __repr__(self):
        if type(self.cdr) is tuple:
            return "[%s %s" % (repr(self.car), continue_repr(self.cdr, ']'))
        elif type(self.cdr) is PairNode:
            return "[%s %s" % (repr(self.car), continue_repr(self.cdr.sexp, ']'))
        elif self.cdr is nil:
            return "[%s]" % repr(self.car)
        else:
            return "[%s | %s]" % (repr(self.car), repr(self.cdr))
    def __len__(self):
        return len(self.sexp)
    def __eq__(self, other):
        return type(other) is PairNode and self.sexp == other.sexp

class IdentifierNode(Node):
    def __init__(self, token):
        self.identifier = token
    def __repr__(self):
        return self.identifier
    def __eq__(self, other):
        return type(other) is IdentifierNode and self.identifier == other.identifier

class NumericLiteralNode(Node):
    def __init__(self, token):
        self.num = int(token)
    def __repr__(self):
        return repr(self.num)
    def __eq__(self, other):
        return type(other) is NumericLiteralNode and self.num == other.num


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

    return (constructor(*parse(form_tokens)), len(form_tokens) + 1) # +1 to account for the closing paren/bracket/whatever

def parse_single_token(token):
    assert token not in matched_tokens

    if re.match(r'\d+', token):
        return NumericLiteralNode(token)
    if token == PAIR_CDR_TOKEN:
        return PAIR_CDR_TOKEN
    return IdentifierNode(token)

matched_tokens = {
    '(': (')', FormNode, lambda: nil), # this should actually throw an exception, but i'm allowing it for now...makes sense if nil can be used as a function
    '[': (']', PairNode, lambda: nil)
}

def parse(tokens): # converts token stream to s-expressions, parses numeric literals, etc
    if len(tokens) == 0:
        return []

    first = tokens[0]

    if first in matched_tokens:
        matched_token, tokens_consumed = read_matched_code(tokens[1:], first, *matched_tokens[first])
        return [matched_token] + parse(tokens[1 + tokens_consumed:])

    return [parse_single_token(first)] + parse(tokens[1:])

def read(code):
    return parse(lex(code))

