from reader import nil, read, FormNode

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

def eval_node(node, scope):
    assert node is not nil

    if type(node) is FormNode:
        fn = scope.get(node.car)
        return fn(node.cdr, scope)
    elif type(node) is str:
        return scope.get(node)
    else:
        raise Exception("I don't know how to do eval %s" % repr(node))

root = Scope({
    'print': lambda arg, scope: print(eval_node(arg[0], scope)),
    'add': lambda arg, scope: arg[0] + arg[1][0],
    'id': lambda arg, scope: arg[0],
    'nil': nil
}, None)

def isheval(code):
    for node in read(code):
        eval_node(node, root)
    return 'if you were expecting a return value here you should probs implement that'
