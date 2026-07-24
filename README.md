# tinypbn: A pedagogical Programming by Navigation system in ~50 lines of Python

**WORK IN PROGRESS! :-)**

Underspecifications are everywhere!

- The experiment a biologist runs in the wet lab is an underspecification for
  the actual computational analysis the scientist wants to run on their data.
- In a proof search system like [Rust's trait system](https://doc.rust-lang.org/book/ch10-02-traits.html) or [Aesop tactic](https://github.com/leanprover-community/aesop) for [Lean](https://lean-lang.org/),
  a failing proof search is an underspecification for the modifications the programmer needs to make to the underlying proof system in order for the proof search to go through (_e.g._, implementing Rust traits or proving Lean lemmas)
- In a user-schedulable language like [Halide](https://halide-lang.org/),
  a program and an initial schedule are an underspecification for a refined
  schedule that a performance engineer actually wants.
- A merge conflict is an underspecification for the particular resolution the programmer desires.
- A program is an underspecification for all programs that are equivalent to it. (This is the premise of optimizing compilers!)

Even when you think you have a precise logical specification, odds are you are actually still dealing with an underspecification.
Consider the venerable sorting algorithm, and it's traditional logical specification:
forall i = 0...len(out)-1 : out[i] < out[i+1] AND
exists permutation sigma : s.t out = in o sigma.
This precise logical specification specifies bubble sort, insertion sort, selection sort, merge sort, heap sort, quick sort, ... and so on!

But in all of the above cases, we often want to arrive at a *particular* solution to the original underspecification.

We can do so view a process of **specification refinement.**
[Programming by Navigation](https://dl.acm.org/doi/10.1145/3729264) is a
technique I've been working on to support programmers interactively refine
underspecifications.

Let's dive in and make a tiny Programming by Navigation system. To fit in this
short post, it'll be limited and slow, but it will capture some of the core
essence of Programming by Navigation!

* * *

## Expressions: The programs we'll be generating

Expressions in our language will be either a literal
integer, a string representing a variable, a hole (represented as `...` in Python), or
an operation applied to a set of arguments (represented as a tuple whosse first component is the operator name and whose remaining components are the arguments).
Operators will just be negation, addition, and multiplication. Because our expressions can have holes in them (_i.e._, they can be incompelte), we'll call them "sketches."

We'll start by defining our evaluation function.

```python
def eval(env, sketch):
    if isinstance(sketch, int):
        return sketch
    elif isinstance(sketch, str):
        return env[sketch]
    elif sketch == ...:
        return float("nan")
    elif sketch[0] == "negate":
        return -eval(env, sketch[1])
    elif sketch[0] == "+":
        return eval(env, sketch[1]) + eval(env, sketch[2])
    elif sketch[0] == "*":
        return eval(env, sketch[1]) * eval(env, sketch[2])
```

If you've never written a programming language before—congrats! You've just
written your very first interpreter for a simple programming language. It all
starts with a function like this!

## Specifications: Our notion of validity for expressions

Next, we'll take input-output example satisfaction as our notion of validity for expressions.
A specification will be represented as a list of pairs of input environments and output values, where input environments are a dictionary
mapping variable names (strings) to values (integers), and output values are simply integers.

We can check if a sketch satisfies a specification by simply checking if evaluating it in each input environment results in the corresponding output value.

```python
def satisfies(spec, sketch):
    return all(eval(env, sketch) == out for env, out in spec)
```

