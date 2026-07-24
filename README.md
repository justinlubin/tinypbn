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

## Expressions, _a.k.a._ the programs we'll be generating

Expressions in our language will be either a literal
integer, a string representing a variable, a hole (represented as `...` in Python), or
an operation applied to a set of arguments (represented as a tuple whosse first component is the operator name and whose remaining components are the arguments).
Operators will just be negation, addition, and multiplication. Because our expressions can have holes in them (_i.e._, they can be incompelte), we'll call them "sketches."

We'll start by defining our evaluation function. Its only quirk is that
evaluating a hole results in a floating point NaN value, which will propagate
through all subsequent operations. That means that any sketch with a hole in it
will evaluate to NaN.

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

**Question to ponder.** What would obstacle might we run into if we evaluate a very, very large term? (Try it!) How could we avoid this obstacle?

## Specifications, _a.k.a._ our notion of validity for expressions

Next, we'll take input-output example satisfaction as our notion of validity for expressions.
A specification will be represented as a list of pairs of input environments and output values, where input environments are a dictionary
mapping variable names (strings) to values (integers), and output values are simply integers.

We can check if a sketch satisfies a specification by simply checking if evaluating it in each input environment results in the corresponding output value.

```python
def satisfies(spec, sketch):
    return all(eval(env, sketch) == out for env, out in spec)
```

Because programs with holes evaluate NaN and we require that output values are integers, only programs without holes can satisfy a non-empty specification.

**Question to ponder.** We've discussed logical specifications and input-output example specifications. What other kinds of specifications can you think of? Additionally, are there any variants of these two kinds of specification that seem interesting to you?

## Our search space of expressions

For simplicity, we'll make some restrictions about the possible expressions we'll
generate. In particular, we'll only consider expressions:
1. Whose size is at most 6
2. Whose integer literals are restricted to 0, 1, 2, and 3
3. Whose variables are restricted to the single variable `in`

First, we can operationalize our notion of size.

```python
def size(sketch):
    if isinstance(sketch, tuple):
        return sum(map(size, sketch))
    return 1
```

Next, we get to the most complicated function in our implementation: top-down left-to-right
expansion of our expression grammar. This function will take in a sketch and
return a list of possible "expansions" of that sketch, where each expansion is
the result of replacing the left-most hole in the sketch with all possible expression "heads" in our language,
where a head is either an integer literal, variable, or the application of an operator to (the correct number of) holes.

```python
def expand(sketch):
    if size(sketch) >= 6:
        return []
    elif sketch == ...:
        return [0, 1, 2, 3, "in", ("negate", ...), ("+", ..., ...), ("*", ..., ...)]
    elif isinstance(sketch, tuple):
        head = sketch[0]
        args = sketch[1:]
        for i, arg in enumerate(args):
            expansions = expand(arg)
            if expansions:
                return [(head,) + args[:i] + (e,) + args[i + 1 :] for e in expansions]
    return []
```

Using these building blocks, we can write a traditional program synthesis algorithm
in just a few lines of code! It will be a worklist algorithm, where we'll start
at a user-provided sketch and repeatedly expand the head of the worklist until
we find a sketch that matches the provided specification.

```python
def fill(spec, sketch):
    worklist = [sketch]
    while worklist:
        candidate = worklist.pop(0)
        if satisfies(spec, candidate):
            return candidate
        worklist.extend(expand(candidate))
```

Because of our restrictions at the start of this section, there are only
finitely-many possible expressions. Therefore, because an expression only ever
gets added to the worklist at most once, this algorithm will always terminate.

**Exercise.** Prove that an expression only ever gets added to the worklist at most once.

**Exercise.** Prove that if there is a satisfying solution to the specification in the search space,
`fill` will return such a solution.

**Question to ponder.** What happens if there is no satisfying solution? How could you speed up this case?

**Question to ponder.** What would happen if we removed the restrictions at the start of this section?

**Question to ponder.** Will adding more examples increase or decrease the running time of
this algorithm? Are there ways that you could imagine tweaking this algorithm to change your answer to this question?

**Exercise.** `fill`, as implemented, takes what is called a top-down term enumeration strategy.
Why do you think it's called that? Think about what a bottom-up strategy would look like and implement it.
_Hint:_ The implementation should not rely on `expand` or any other helper function, and should be quite a bit simpler than the
code we have here; I would have used bottom-up enumeration here if we didn't need the `expand` function later on!

