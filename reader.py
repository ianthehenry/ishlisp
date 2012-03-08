# imports below

PAIR_CDR_TOKEN = '|'

class Node:
    pass

class ValueNode(Node):
    def __init__(self, name, value):
        assert type(name) is str
        self.value = value
        self.name = name
    def __repr__(self):
        return self.name
    def __str__(self):
        return "(ValueNode '%s')" % self.name
    def __eq__(self, other):
        return type(other) is ValueNode and self.value == other.value

class BinaryOperatorNode(Node):
    def __init__(self, token, special_form, precedence, associativity):
        self.token = token
        self.special_form = special_form
        self.precedence = precedence
        self.associativity = associativity
    def __repr__(self):
        return self.token
    def __str__(self):
        return "BinaryOperatorNode '%s'" % self.token

class UnaryOperatorNode(Node):
    def __init__(self, token, special_form):
        self.token = token
        self.special_form = special_form
    def __repr__(self):
        return self.token
    def __str__(self):
        return "UnaryOperatorNode '%s'" % self.token

def parse_forms(lst, is_form_node = True):
    constructor = FormNode if is_form_node else Pair

    if type(lst) is not tuple:
        assert lst is nil or isinstance(lst, Node)
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
        return "(FormNode %s %s)" % (str(self.car), str(self.cdr))
    def __eq__(self, other):
        return type(other) is FormNode and self.car == other.car and self.cdr == other.cdr

class IdentifierNode(Node):
    def __init__(self, token):
        assert type(token) is str
        self.identifier = token
    def __repr__(self):
        return self.identifier
    def __str__(self):
        return "(IdentifierNode %s)" % self.identifier
    def __eq__(self, other):
        return type(other) is IdentifierNode and self.identifier == other.identifier

class SymbolLiteralNode(Node):
    def __init__(self, token):
        assert type(token) is str
        self.value = token[1:]
    def __repr__(self):
        return "#%s" % self.value
    def __str__(self):
        return "(SymbolLiteralNode %s)" % self.value
    def __eq__(self, other):
        return type(other) is SymbolLiteralNode and self.value == other.value

class NumericLiteralNode(Node):
    def __init__(self, token):
        assert type(token) is str
        self.num = int(token)
    def __repr__(self):
        return repr(self.num)
    def __str__(self):
        return "(NumericLiteralNode '%s')" % repr(self.num)
    def __eq__(self, other):
        return type(other) is NumericLiteralNode and self.num == other.num

def lookahead(indexable):
    i = 0
    while i < len(indexable):
        yield (indexable[i], indexable[i + 1] if i < len(indexable) - 1 else None)
        i += 1

def lex(code): # converts string to tokens, currently represented as simple strings
    boundaries = set([' ', '\t', '\n', ',', PAIR_CDR_TOKEN]) | \
        BINARY_OPERATORS.keys() | \
        UNARY_OPERATORS.keys() | \
        MATCHED_TOKENS.keys() | \
        set([end for end, _, _ in MATCHED_TOKENS.values()])
    tokens = []
    def end_token(char_list):
        token = ''.join(char_list)
        if not re.match(r'^[ \t\n,]*$', token):
            tokens.append(token)
    current_token = []
    skip_character = False
    for current_char, next_char in lookahead(code):
        if skip_character:
            skip_character = False
            continue
        if next_char is not None and current_char + next_char in boundaries:
            end_token(current_token)
            end_token([current_char, next_char])
            current_token = []
            skip_character = True
        elif current_char in boundaries:
            end_token(current_token)
            end_token([current_char])
            current_token = []
        else:
            current_token += current_char
    end_token(current_token)
    return tokens

def read_matched_code(tokens, end, constructor, empty_constructor):
    increasers = set([key for key in MATCHED_TOKENS if MATCHED_TOKENS[key][0] == end])
    nesting_depth = 1
    def pred(token):
        nonlocal nesting_depth
        if token in increasers:
            nesting_depth += 1
        elif token == end:
            nesting_depth -= 1
            return nesting_depth > 0
        return True

    form_tokens = list(takewhile(pred, tokens))
    if nesting_depth != 0:
        raise Exception("Unbalanced tokens")

    if len(form_tokens) == 0:
        return (empty_constructor(), 1)

    return (constructor(*parse_and_expand(form_tokens)), len(form_tokens) + 1) # +1 to account for the closing paren/bracket/whatever

def parse_single_token(token):
    assert token not in MATCHED_TOKENS

    if re.match(r'^\d+$', token):
        return NumericLiteralNode(token)
    if token == PAIR_CDR_TOKEN:
        return PAIR_CDR_TOKEN
    if token in BINARY_OPERATORS:
        return BINARY_OPERATORS[token]
    if token in UNARY_OPERATORS:
        return UNARY_OPERATORS[token]
    if re.match(r'^#[A-Za-z0-9-]+$', token):
        return SymbolLiteralNode(token)

    return IdentifierNode(token)

# TODO: get rid of the whole "empty constructor" nonsense
MATCHED_TOKENS = {
    '(': (')', lambda *sexp: parse_forms(sexp), lambda: ValueNode('_nil', nil)), # this should actually throw an exception, but i'm allowing it for now...makes sense if nil can be used as a function
    '[': (']',
        lambda *sexp: FormNode(ValueNode('_list', specials.list_), parse_forms(sexp, False)),
        lambda: ValueNode('_nil', nil)),
    '#[': (']',
        lambda *sexp: FormNode(ValueNode('_array', specials.array), parse_forms(sexp, False)),
        lambda: FormNode(ValueNode('_array', specials.array), nil)),
    '#(': (')',
        lambda *sexp: FormNode(ValueNode('_sfn', specials.function_shorthand), parse_forms(sexp, False)),
        lambda: ValueNode('_nil', nil)), # TODO: this should be the void function
    '{': ('}',
        lambda *sexp: FormNode(ValueNode('_object', specials.object), parse_forms(sexp, False)),
        lambda: FormNode(ValueNode('_object', specials.object), nil))
}

def reverse_iterator(items):
    i = len(items) - 1
    while i >= 0:
        yield items[i]
        i -= 1

def expand_unary_operators(nodes):
    output = []
    i = 0

    def pop_node():
        nonlocal i
        if i >= len(nodes):
            raise Exception("Unary operator must come before something")
        node = nodes[i]
        i += 1
        if type(node) is UnaryOperatorNode:
            return parse_forms((node.special_form, pop_node()))
        else:
            return node

    while i < len(nodes):
        output.append(pop_node())

    return output

def expand_binary_operators(nodes):
    output_queue = []
    operator_stack = []
    last_node = None

    def is_space(node):
        return type(last_node) is not BinaryOperatorNode and type(node) is not BinaryOperatorNode

    def drain_operator_stack(node = None):
        def should_drain():
            if len(operator_stack) == 0:
                return False
            if node is None:
                return True
            if node.associativity == 'left':
                return operator_stack[-1].precedence < node.precedence
            else:
                return operator_stack[-1].precedence <= node.precedence
        while should_drain():
            output_queue.append(operator_stack.pop())

    for node in reverse_iterator(nodes):
        if is_space(node):
            drain_operator_stack()
        if type(node) is BinaryOperatorNode:
            drain_operator_stack(node)
            operator_stack.append(node)
        else:
            output_queue.append(node)
        last_node = node

    drain_operator_stack()

    def pop_node():
        node = output_queue.pop()
        if type(node) is BinaryOperatorNode:
            return parse_forms((node.special_form, pop_node(), pop_node()))
        else:
            return node

    result = []
    while len(output_queue) > 0:
        result.append(pop_node())

    return result

def parse(tokens): # converts token stream to s-expressions, parses numeric literals, etc
    if len(tokens) == 0:
        return []

    first = tokens[0]

    if first in MATCHED_TOKENS:
        matched_token, tokens_consumed = read_matched_code(tokens[1:], *MATCHED_TOKENS[first])
        return [matched_token] + parse(tokens[1 + tokens_consumed:])

    return [parse_single_token(first)] + parse(tokens[1:])

def parse_and_expand(tokens):
    return expand_binary_operators(expand_unary_operators(parse(tokens)))

def read(code):
    return parse_and_expand(lex(code))

import specials
import re
from core import Pair, nil
from itertools import takewhile

BINARY_OPERATORS = {
    ':': BinaryOperatorNode(':', ValueNode('_cons', specials.cons), 2, 'right'),
    '.': BinaryOperatorNode('.', ValueNode('_get', specials.get), 1, 'left'),
    '::': BinaryOperatorNode('::', ValueNode('_pattern-with-predicate', specials.pattern_with_predicate), 4, 'left'),
    '=': BinaryOperatorNode('=', ValueNode('_pattern-with-default', specials.pattern_with_default), 4, 'left'),
    '/': BinaryOperatorNode('/', ValueNode('_slash', specials.slash), 3, 'left'),
}

UNARY_OPERATORS = {
    '~': UnaryOperatorNode('~', ValueNode('_id', specials.id)),
}
