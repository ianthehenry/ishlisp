# ishlisp

A pretty awful interpreter for a semi-lisp-like, written in Python 3.

It was written mostly in one sitting. I was actually having so much fun with it that I stayed up all night on a Friday, slept all day Saturday, and then stayed up all night working on it again.

This is not advised.

But it was a fun project. Here's a run-down of the insane amalgam of unconnected features it has:

## pattern matching

    (def heads (fn [x:xs y:ys] [x y]))

- Arbitrary predicates: `(fn [a::pred?] foo)`
- Patterns that can fail with a default value: `(fn [a b=3] (a + b))`
- List destructuring: `(fn first:rest first)` or `(fn [first | rest] first)`
- Multiple patterns: `(fn all/[first | rest] first:all)`

## overloaded functions

What would patterns be without "multifunctions"?

    (def a (mfn
        ([a] (add a 1))
        ([a b] (add a b))))

## first class patterns

Because it's a dynamic language, it seemed silly to do it any other way. The `pattern` special form can be used to parse patterns:

    > (def my-pattern (pattern [a::even? b/c]))

Which can then be evaluated dynamically:

    > (match? my-pattern [1 2])
    true

I don't think I ever implemented dynamically extracting scope values from patterns, but it would be trivial to do that, due to the duality of environments and objects explained below.

## binary operators

One of the goals was to make the language *not very lisp looking*, by providing syntax that made it look more like a traditional C-like language.

One part of this is support for binary operators. This was [fun to implement](http://en.wikipedia.org/wiki/Shunting-yard_algorithm), and allows you to write code like this:

    (a = 1:2:[])

Instead of this:

    (def a (cons 1 (cons 2 nil)))

The goal was not to replace all prefix functions (all math operations are still prefix, for example), but merely to support some nicer-looking constructs for key lookup and pattern matching. Also to use the word "shunt" more.

The supported operators were:

- `a:b`, an infix synonym for `cons`.
- `a.b`, an infix synonym for `get`.
- `a::b`, an infix synonym for `pattern-with-predicate`.
- `a=b`, an infix synonym for `def`.
- `a/b`, an infix synonym for `pattern-with-alias`.

## paren insertion

Paren insertion was an optional preprocessing step, that allowed you to write code whitespace sensitive code like this:

    foo = $ fn [x]
      something

Instead of the equivalent:

    (foo = (fn [x]
      (something)))

The `=` sugar was intended to be used in this way, as `(foo = 123)` is not better than `(def foo 123)`, but `foo = 123` is slightly nicer in some situations.

It made whitespace significant, in an attempt to appeal non-paren-friendly developers. So it takes the most controversial syntactic choice of all time and replaces it with the very close second. Yeah.

There was a unary macro, `~`, that (basically) suppressed this behavior for a single line:

    foo = $ fn [x]
      ~something
    
    (foo = (fn [x]
      something))

This turned out to not be a very good idea, so we're not going to talk about it any more.

## other goofy syntax

- Symbol literal notation: `#foo`
- Comment notation: `# foo`
- List literal notation: `[1 2 3]`
- Array literal notation: `#[1 2 3]`
- Object literal notation: `{ foo: 2, bar: 4 }`
- Dictionary literal notation: `#{ 1: 2, "foo": 3, #bar: 4 }`

Note that `,` is a whitespace character, and that `:` is just infix `cons`.

## data

The two core data types are pairs (traditional lisp cons cells) and "scopes", or objects-with-prototypes.

The idea that the current scope of a function was just an object with a pointer to the parent scope was important to me at the time, as it unified contexts with objects with differential inheritance.

There were also dictionaries and arrays, which correspond to Python's dictionaries and lists, and `void`, which corresponds to Python's `None`. It's what a function returns when it has nothing else to return.

Like I said, lotta ideas thrown into this language.

## prototypal inheritance

Because the language supported closures with mutable contexts, prototypal inheritance sort of happened for free. So I ran with it.

I spent a long time trying to reify these two ideas into an elegant way to move between objects and scopes to enable some sort of new-style of metaprogramming. I was unable to squeeze anything interesting out of it.

## lazy evaluation

Because "pair" was an interface, it didn't necessarily have to be an *actual* cons cell, but could instead be an object with an overloaded getter for the `cdr`. This sort of list-of-thunks can be used to emulate something sort-of-like-a-generator:

    (def map (mfn
        ([f []] [])
        ([f x:xs] (f x):(delay (map f xs)))))

Thunks are a special part of the language inasmuch as the default `get` special-cases them (see "object story" for more on that). Otherwise they're equivalent to normal lambdas, but with a distinct type.

## callables

Any object that provides a `call` method can be invoked, not just functions. A default implementation of `call` exists for `Pair`s: it's function composition.

    > (def double (fn [x] (* 2 x)))
    > (def add +)
    > (double:add 4 1)
    10

Or merely:

    > ((* 2):+ 4 1)
    10

(Assuming `*` were a curried function.)

The only other type in the standard library that's callable, apart from functions, are bound methods.

## methods

Methods are like function-factories: you can't invoke them directly, but if you supply them a context you can get a function back (it's not actually a function, it's actually a bound method, but it's callable, so whatever).

Because of the way method lookup works, it's useful to have this as an explicity different type from a function.

    > (def obj { foo: (md [x] (+ x @y)), y: 10 })
    > (obj.foo 3)
    13

When a method body is executed, the scope begins with an identifier called `this`, in addition to any that result from pattern matching the arguments. This is more desirable than having an explicit first argument, as a methods can be invoked without lists as arguments.

There is a unary operator, `@foo`, that expands to `(get this #foo)`.

## the object story

The object model is based on prototypal inheritance. On the surface it looks sort of similar to JavaScript, but properties and contexts are very different.

(This section is written from memory. I may have done dumb shit in the actual implementation like make `get-slot` a method and deliberately chosen to forget it. This is how the object model *should* behave.)

There are primitive functions `get-slot`, `lookup-slot`, and `set-slot` that... get and set slots on objects. Slots are always named by symbols. There is no way to control access to objects, make them immutable, or anything like that if you use the `set-slot` interface. An object's prototype is not a slot and can never be changed.

`get-slot` returns the value of a slot, walking the prototype chain if necessary, and throws an exception if it doesn't exist. `set-slot` sets a slot and never involves the prototype chain.

(Shortly after writing this interpreter I realized the importance for a distinction between `get` (no prototype chain) and `lookup` (prototype chain), and between `set` and `upset` (for manipulating variables in scope, and thus objects) but you will not find those distinctions in this implementation.)

The base `Object` that objects inherit from by default includes a `get` method.

So when you type:

    (foo.bar 1 2 3)

Which expands to:

    ((get foo #bar) 1 2 3)

The following things happen:

- The `get` *function* invokes `get-slot` to look up the `get` *method* on the object `foo`.
- `foo`'s `get` "method" is invoked with the argument list `[foo #bar]`
- The default behavior of `get` is to invoke `get-slot`, turning exceptions into `void`s, and performing the following logic on the return value:
    - if it's a method, return the method bound to `foo`
    - if it's a thunk, force the thunk and return its value
    - if it's anything else, return the value unchanged
- In this case we assume it's a method, so it returns a bound version of `foo`'s `bar` method.
- That bound method is then invoked with an arguments list of `[1 2 3]`

In this way there's no dynamic, language-level `this`, thunks can emulate built-ins like `cdr`, and `get-slot` is always available to access unbound functions or thunks with resolving them.

The cost is that a simple method invocation is very expensive, all just to support dynamic overriding of `get`.

Again, memory. It might actually behave differntly. I'm not saying any of this is a good idea; this was just a weekend project I did for fun three years ago.

## exceptions

The language is supposed to support a value-based-exception mechanism, but I don't think that I got that far in this implementation.
