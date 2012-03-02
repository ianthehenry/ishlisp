from reader import nil, read, FormNode, PairNode, IdentifierNode, NumericLiteralNode

class Scope:
    def __init__(self, dict, parent):
        self.dict = dict
        self.parent = parent
    def get(self, identifier):
        if identifier in self.dict:
            return self.dict[identifier]
        if self.parent is None:
            print(self.dict)
            raise Exception("identifier '%s' is not in scope" % identifier)
        return self.parent.get(identifier)

def eval_node(node, scope):
    assert node is not nil

    if type(node) is FormNode:
        assert type(node.car) is IdentifierNode
        fn = scope.get(node.car.identifier)
        return fn(node.cdr, scope)
    elif type(node) is IdentifierNode:
        return scope.get(node.identifier)
    elif type(node) is NumericLiteralNode:
        return node.num
    else:
        raise Exception("I don't know how to do eval %s" % repr(node))

root = Scope({
    'print': lambda arg, scope: print(eval_node(arg[0], scope)),
    'add': lambda arg, scope: eval_node(arg[0], scope) + eval_node(arg[1][0], scope),
    'id': lambda arg, scope: arg[0],
    'nil': nil
}, None)

def isheval(code):
    for node in read(code):
        eval_node(node, root)
    return 'if you were expecting a return value here you should probs implement that'
