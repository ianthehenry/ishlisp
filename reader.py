import re
from core import Pair, nil
from itertools import takewhile

PAIR_CDR_TOKEN = '|'

def parse_forms(lst, is_form_node = True):
    constructor = FormNode if is_form_node else Pair

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
        return constructor(lst[0], lst[2])

    return constructor(parse_forms(lst[0]), parse_forms(lst[1:], False))

class Node:
    pass

def get_form_repr(form_or_pair):
    prefix = '(' if type(form_or_pair) is FormNode else ''
    if form_or_pair.cdr is nil:
        return "%s%s)" % (prefix, repr(form_or_pair.car))
    elif type(form_or_pair.cdr) is Pair:
        return "%s%s %s" % (prefix, repr(form_or_pair.car), get_form_repr(form_or_pair.cdr))
    else:
        return "%s%s | %s)" % (prefix, repr(form_or_pair.car), repr(form_or_pair.cdr))

# should this be a subclass of Pair?
class FormNode(Node):
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr
    def __repr__(self):
        return get_form_repr(self)
    def __len__(self):
        return len(self.sexp)
    def __str__(self):
        return "FormNode '[%s | %s]'" % (str(self.car), str(self.cdr))
    def __eq__(self, other):
        return type(other) is FormNode and self.car == other.car and self.cdr == other.cdr

class IdentifierNode(Node):
    def __init__(self, token):
        assert type(token) is str
        self.identifier = token
    def __repr__(self):
        return self.identifier
    def __str__(self):
        return "IdentifierNode %s" % repr(self.identifier)
    def __eq__(self, other):
        return type(other) is IdentifierNode and self.identifier == other.identifier

class NumericLiteralNode(Node):
    def __init__(self, token):
        assert type(token) is str
        self.num = int(token)
    def __repr__(self):
        return repr(self.num)
    def __str__(self):
        return "NumericLiteralNode '%s'" % repr(self.num)
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
    '(': (')', lambda *sexp: parse_forms(sexp), lambda: nil), # this should actually throw an exception, but i'm allowing it for now...makes sense if nil can be used as a function
    '[': (']', lambda *sexp: FormNode(IdentifierNode('list'), parse_forms(sexp, False)), lambda: nil)
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
