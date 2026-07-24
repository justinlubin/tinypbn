# tinypbn: A pedagogical Programming by Navigation system in ~50 lines of Python

**Warning:** This is a work-in-progress!

- If you want to dive into the code, check out
  [`tinypbn.py`](./tinypbn.py)!
- If you want a
  [literate programming](https://en.wikipedia.org/wiki/Literate_programming)
  exposition of the code, read on!

In any case, please feel free to email me at
[justinlubin@berkeley.edu](mailto://justinlubin@berkeley.edu)
to chat about your thoughts! I'm happy to discuss the "questions to ponder"
peppered throughout the essay below or anything else you'd like to chat about!

* * *

Underspecifications are everywhere!

- The experiment a biologist runs in the wet lab is an underspecification for
  the actual computational analysis the scientist wants to run on their data.
- In a proof search system like
  [Rust's trait system](https://doc.rust-lang.org/book/ch10-02-traits.html)
  or the
  [Aesop tactic](https://github.com/leanprover-community/aesop)
  for
  [Lean](https://lean-lang.org/),
  a failing proof search is an underspecification for the modifications the
  programmer needs to make to the underlying proof system in order for the proof
  search to go through (_e.g._, implementing Rust traits or proving Lean lemmas)
- In a user-schedulable language like [Halide](https://halide-lang.org/),
  a program and an initial schedule are an underspecification for a refined
  schedule that a performance engineer actually wants.
- A merge conflict is an underspecification for the particular resolution the
  programmer desires.
- A program is an underspecification for all programs that are equivalent to it.
  This is (roughly) the premise of compilers!

Even when you think you have a precise logical specification, I'd bet you're
still actually dealing with an underspecification. Consider the traditional
logical specification for the venerable sorting algorithm taking in an array
`in` and returning an array `out`:

    ∀ i = 1, ..., len(out) - 1. out[i] < out[i + 1] ∧
    ∃ permutation σ. out = in ◦ σ

This precise logical specification specifies bubble sort, insertion sort,
selection sort, merge sort, heap sort, quick sort, ... and so on! (Perhaps it's
not so precise after all?)

In all of the above cases, we often want to arrive at a *particular* solution to
the original underspecification. We can view this as a process of
*specification refinement*.
[**Programming by Navigation**](https://dl.acm.org/doi/10.1145/3729264) is a
technique I've been working on to support programmers interactively refine
underspecifications. What's neat about it is that, at each step of the
refinement process, a Programming by Navigation system is required to give you
a set of possible refinements ("next steps") that satisfies:

- **Strong Soundness:** All provided steps are en route to a valid solution.
- **Strong Completeness:** All remaining valid solutions are reachable by
  choosing one of the provided steps.

Strong Soundness means you won't go down a rabbit hole of exploring invalid
program space. Strong Completeness means the system won't take any possible
solutions away from you. To achieve these guarantees in practice can be
[pretty](https://dl.acm.org/doi/10.1145/3729264)
[involved](https://dl.acm.org/doi/10.1145/3808344),
but I
think that my ~50 line [`tinypbn.py`](./tinypbn.py) file demonstrates some of
its core essence! Let's dive into exploring it together now.

**Pro tip:** Before reading the implementation of each function,
*try to implement it yourself!!* I promise, it's really fun!!
### Expressions, _a.k.a._ the programs we'll be generating

Expressions in our language will be either:

- A literal integer,
- A variable (represented in Python as a string),
- A hole signifying an incomplete program fragment (represented in Python as
  `...` in Python, also called
  [Ellipsis](https://docs.python.org/dev/library/constants.html#Ellipsis)), or
- An operation applied to a list of arguments (represented as a tuple whose
  first argument is the operator and whose remaining components are the
  arguments). Operations will be negation (`negate`, one argument), addition
  (`+`, two arguments), and multiplication (`*`, two arguments).

Because our expressions can have holes in them, we'll call them "sketches,"
following [tradition](https://people.csail.mit.edu/asolar/SynthesisCourse/Lecture7.htm).

We'll start by defining our evaluation function. Because sketches can
have variables, our evaluation function will need access to an environment
(represented in Python as a dictionary) that maps variable names (strings)
to values (integers). The only other quirk is that evaluating a hole results
in a floating point NaN value, which will propagate through all subsequent
operations. This means that any sketch with a hole in it will evaluate to NaN.

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

- **Question to ponder #1:** What obstacle might we run into if we evaluate a
very, very large expression? (Try it!) How could we avoid this obstacle?

### Specifications, _a.k.a._ our notion of validity for expressions

Next, we'll take input-output example satisfaction as our notion of validity for
expressions. We'll represent such a specification as a list of pairs, where:

- The first component of the pair is an input environment (a dictionary, as
  above), and
- The second component of the pair is an output value (integer) that a sketch
  should evaluate to in the given input environment.

(**Pause!** How would you implement a function that checks this notion of
satisfaction?)

We can check if a sketch satisfies a specification by checking if evaluating it
in each input environment results in the corresponding output value.

```python
def satisfies(spec, sketch):
    return all(eval(env, sketch) == out for env, out in spec)
```

- **Question to ponder #2:** Using this notion of satisfaction, what kind(s) of
specifications can sketches with holes in them satisfy?
- **Question to ponder #3:** We've discussed logical specifications and
input-output example specifications. What other kinds of specifications can
you think of? Additionally, are there any variants of these two kinds of
specification that seem interesting to you?

### Our search space of expressions

For simplicity, we'll make some restrictions about the possible expressions we'll
generate. In particular, we'll only consider expressions:

- With size is at most 6,
- With integer literals restricted to 0, 1, 2, and 3, and
- With variables restricted to the single variable `in`.

First, let's operationalize "size."

```python
def size(sketch):
    if isinstance(sketch, tuple):
        return sum(map(size, sketch))
    return 1
```

With that, we've arrived at the most complicated function in our implementation:
top-down left-o-right expansion of our sketch grammar. This function will take
in a sketch and return a list of possible "expansions" of that sketch, where
each expansion is the result of replacing the _left-most hole_ in the sketch
with all possible "immediate expressions" in our language, where an "immediate
expression" is either:

- An integer literal,
- A variable, or
- The application of an operator to the correct number of holes.

If there are no holes (or the sketch is already at our size limit), the function
should return no expansions.

(**Pause!** If you want a bit of a challenge, try to implement this function!)

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

Using these building blocks, we can write a traditional program synthesis
algorithm called "top-down enumeration" in just a few lines of code! It will be
a worklist algorithm where we start with a user-provided sketch and repeatedly
`expand` the head of the worklist until we find a sketch that matches the
provided specification.

(**Pause!** Try to implement this function!)

```python
def fill(spec, sketch):
    worklist = [sketch]
    while worklist:
        candidate = worklist.pop(0)
        if satisfies(spec, candidate):
            return candidate
        worklist.extend(expand(candidate))
```

- **Question to ponder #4:** How many times can a given expression be added to the
worklist?
- **Question to ponder #5:** Does this algorithm always terminate? Why or why
not?
- **Question to ponder #6:** If there is a satisfying solution to the
specification in the search space, will `fill` return it? If so, why? If not,
can you think of a rewording of this property to make it true?
- **Question to ponder #7:** What would happen if our `expand` function provided
expansions on more than just the left-most hole? How (if at all) do your answers
to the previous questions change?
- **Question to ponder #8:** What would happen if we removed the restrictions at
the start of this section? How (if at all) do your answers to the previous
questions change?
- **Question to ponder #9:** Will `fill` be faster when there is a satisfying
solution or when there is not a satisfying solution? How could you speed up the
slower case?
- **Question to ponder #10:** Will adding more examples increase or decrease the
running time of this algorithm? Are there ways that you could imagine tweaking
this algorithm (without changing its input-output behavior) to change your
answer to this question?
- **Question to ponder #11:** We discussed that `fill`, as implemented, takes
what is called a top-down enumeration strategy. Why do you think it's called
that? Think about what a "bottom-up" enumeration strategy would look like and
implement it. _Hint:_ The implementation should not rely on `expand` or any
other helper function, and in fact should be quite a bit simpler than the code
for `expand` and `fill`; I would have used bottom-up enumeration here if we
didn't need the `expand` function later on!
