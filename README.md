# tinypbn: A pedagogical Programming by Navigation system in ~50 lines of Python

- If you want to dive into the code, check out
  [`tinypbn.py`](./tinypbn.py)!
- If you want a
  [literate programming](https://en.wikipedia.org/wiki/Literate_programming)
  exposition of the code, read on!

In any case, please feel free to email me at
[justinlubin@berkeley.edu](mailto://justinlubin@berkeley.edu)
to chat about your thoughts! I'm happy to discuss the "questions to ponder"
peppered throughout the post below or anything else you'd like to chat about.

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
- A program is an underspecification for all programs that are semantically
  equivalent (or semantically refine) to it. (This is the premise of compilers!)

Even when you think you have a precise logical specification, I'd bet you're
still actually dealing with an underspecification. Consider the traditional
logical specification for the venerable sorting algorithm taking in an array
`in` and returning an array `out`:

$$ (\forall i \in \{ 1, \ldots{}, \textsf{len}(\texttt{out}) \}.\ \texttt{out}[i] \leq \texttt{out}[i + 1]) \land (\exists \text{ permutation } \sigma.\ \texttt{out} = \texttt{in} \circ \sigma) $$

This logical specification is very precise: disregarding stability, it
completely dictates the input-output behavior of a sorting algorithm. It's also
satisfied by by bubble sort, insertion sort, selection sort, merge sort, heap
sort, quick sort, ... and so on! (Perhaps it's not so precise after all?)

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
solutions away from you.

It looks like this:

![One round of interaction with Programming by Navigation. The system is
required to present the user with only steps en route to a valid solution
(Strong Soundness) while also providing enough steps to reach any valid solution
(Strong Completeness).](pbn.png)

To achieve these guarantees in practice can be
[pretty](https://dl.acm.org/doi/10.1145/3729264)
[involved](https://dl.acm.org/doi/10.1145/3808344),
but I
think that my ~50 line [`tinypbn.py`](./tinypbn.py) file demonstrates some of
the core essence of Programming by Navigation! Let's dive into exploring it
together now.

**Pro tip:** Before reading the implementation of each function,
*try to implement it yourself!!* I promise, it's really fun!!

### Expressions, _a.k.a._ the programs we'll be generating

Expressions in our language will be either:

- A literal integer (represeted in Python as an integer),
- A variable (represented in Python as a string),
- A hole signifying an incomplete program fragment (represented in Python as
  `...` in Python, also called
  [`Ellipsis`](https://docs.python.org/dev/library/constants.html#Ellipsis)), or
- An operation applied to a list of arguments (represented in Python as a tuple
  whose first argument is the operator and whose remaining components are the
  arguments). Operations will be negation (`negate`, one argument), addition
  (`+`, two arguments), and multiplication (`*`, two arguments).

Because our expressions can have holes in them, we'll call them "sketches,"
following [tradition](https://people.csail.mit.edu/asolar/SynthesisCourse/Lecture7.htm).

We'll start by defining our evaluation function. Because sketches can
have variables, our evaluation function will need access to an environment
(represented in Python as a dictionary) that maps variable names (strings)
to values (integers). The only other quirk is that evaluating a hole will result
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

For simplicity, we'll make some restrictions about the possible expressions
we'll generate. In particular, we'll only consider expressions:

- With size is at most 6;
- With integer literals restricted to 0, 1, 2, and 3; and
- With variables restricted to the single variable `in`.

First, let's operationalize "size."

```python
def size(sketch):
    if isinstance(sketch, tuple):
        return sum(map(size, sketch))
    return 1
```

And now, for our next function, we arrive at the most complicated function in
our implementation: top-down left-to-right expansion of our sketch grammar.
This function will take in a sketch and return a list of possible "expansions"
of that sketch, where each expansion is the result of replacing the _left-most
hole_ in the sketch with all possible "immediate expressions" in our language,
where an "immediate expression" is either:

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
algorithm called "top-down enumeration" in just a few lines of code. It will be
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

- **Question to ponder #4:** How many times can a given expression be added to
the worklist in one run of the algorithm?
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
for `expand` and `fill`. (I would have used bottom-up enumeration here if we
didn't need the `expand` function later on!)

### Programming by Navigation, finally!

Everything we've discussed so far has been about standard program semantics
(evaluation) and program synthesis (specifications, satisfaction, and search).

On top of a notion of expressions and validity, Programming by Navigation
requires a notion of **steps** (refinements). Steps will have an associated
semantics that maps a sketch to a new sketch. We'll also require that steps
satisfy certain properties that make them true _refinements_ (in the sense
that each step you take narrows down the possible valid expressions
you can reach), but I'll refer you to Section 3.1 of the
[Programming by Navigation](https://dl.acm.org/doi/10.1145/3729264)
paper for details.

- **Question to ponder #12:** Think of some more traditional processes of
refinement (e.g. logical implication). How would you model that using the
Programming by Navigation framework, which requires expressions, validity (of
expressions), and steps?

In our case, we will choose _top-down left-to-right steps_, the semantics of
which is to replace the left-most hole of a sketch with an immediate expression
(as we defined in the previous section). Implementation-wise, this is a
convenient choice because we already have a function that implements the
semantics of these steps: `expand`!

- **Question to ponder #13:** In this case, our notion of steps coincides
exactly with the enumeration strategy we implemented earlier, but that is simply
for the sake of brevity of implementation. We can define our steps however we
want! What are some other kinds of steps you could imagine? In particular,
what would a notion of "bottom-up" steps look like? It's fun to think about and
tricky to nail down exactly! _Hint:_ It will require a different notion of
expressions.

Now that we have defined steps, the final thing we need to implement for our
Programming by Navigation is a **step provider**: an algorithm that, given a
current working expression, returns a set of steps for the user to choose
between. The user interaction model will look as follows, with the step provider
providing sets of steps $\Sigma$ and the step decider (the user) selecting a
step $\sigma$ from $\Sigma$:

![The step provider provides sets of steps for the step decider to select
between. The process repeats until arriving at the desired expression.](ux.png)

As we discussed at the start of this post, the most interesting part of step
providers is that we will require them satisfy **Strong Soundness** and
**Strong Completeness**.
To give a formal definition of Strong Soundness and Strong Completeness, it is
helpful to formalize the idea we discussed just a moment ago: the "possible
valid expressions you can reach." To capture this idea, we say that the
_completion_ of an expression $e$ is
$\mathcal{C}(e) = \\{e' \mid e \preceq e' \land e' \textsf{ valid} \\}$,
where $e \preceq e'$ if there exists a step between $e$ and $e'$.

Then, given a current working expression $e$, we'll require two properties of
the steps $\Sigma$ the step provider produces:

- **Strong Soundness**: $\mathcal{C}(\sigma e) \neq \varnothing$ for all $\sigma \in \Sigma$.
- **Strong Completeness**: $\bigcup_{\sigma \in \Sigma} \mathcal{C}(\sigma e) \supseteq \mathcal{C}(e) \ \setminus\ \{e\}$

In English, the first property says that, no matter which step you select, the
resulting completion is nonempty. The second property says that every reachable
valid expression is still reachable using one of the provided steps, with the
possible exception of the current working expression itself. This formalization
concretizes the original, intuitive definition at the start of this post!

## Implementing our very first step provider

In the previous section, we discussed what Strong Soundness and Strong
Completeness _are_, but... how do we actually build a step provider that
achieves both of those properties in practice?

I've built a few Programming by Navigation systems now, and in my experience
I've found creating one building block in particular to be invaluable: the
_nonempty-completion oracle_. The idea of the nonempty completion oracle
is to take an expression $e$ and return `True` if its completion is nonempty
(_i.e._, $\mathcal{C}(e) \neq \varnothing$) and `False` otherwise. For the
practical Programming by Navigation systems I've worked on, building a
nonempty-completion oracle has been one of the central technically-challenging
components of the project. However, as we'll see, once you have one, you're
really cooking! And, luckily for us, defining a nonempty-completion oracle for
our pedagogical Programming by Navigation system could not be easier:

```python
def nonempty_completion(spec, sketch):
    return fill(spec, sketch) is not None
```

- **Question to ponder #14:** Why does this function implement a
nonempty-completion oracle? _Hint:_ First, answer questions #5 and #6.

Because in there are only finitely-many possible steps to show the user, our
step provider can simply loop through all possible steps and see if the
resulting expression has a nonempty completion. For brevity, instead of
explicitly representing steps in Python (using a tuple or something similar),
we'll just represent steps as the _result they would have_ on the current
working expression. (This means the user will ultimately select between next
expressions rather than between next steps.)

```python
def provide(spec, sketch):
    return [c for c in expand(sketch) if nonempty_completion(spec, c)]
```

- **Question to ponder #15:** Why does this step provider satisfy Strong
Soundness? Why does this step provider satisfy Strong Completeness?

- **Question to ponder #16:** This particular step provider implements what I
call "classical-constructive" synthesis in the
[Programming by Navigation](https://dl.acm.org/doi/10.1145/3729264);
it uses a nonempty-completion oracle that answers "yes" or "no" (in the style of
classical logic) to arrive at an expression that satisfies the specification (in
the style of constructive logic). But our nonempty-completion oracle
implementation, `nonempty_completion`, is what I would call a _constructive
synthesizer in disguise_---there's nothing classical about it! Why might that
characterization be fair? What are the performance downsides to being
constructive in disguise? And how could you implement an oracle that is not
constructive in disguise?

## Tying it all together with the main loop

We're basically done! All we need to do is hook these components together with
the user's input in a main loop.

(**Pause!** This is a fun one to implement yourself!)

```python
def pbn(spec):
    sketch = ...
    while not satisfies(spec, sketch):
        print(f"Current working expression: {sketch}")
        steps = provide(spec, sketch)
        for i, step in enumerate(steps):
            print(f"  {i}. {step}")
        choice = int(input("Choose a step: "))
        sketch = steps[choice]
    return sketch
```

- **Question to ponder #17** We've spent a lot of time discussing how to
implement step _providers_, but what if the step _decider_ was not a "user" in
the traditional sense? What if it was itself another program? In particular,
consider the following step providers: a random number generator, a
probabilistic model, an AI agent. Can you think of use-cases for each of these
step providers? Can you think of other kinds of step deciders?

- **Question to ponder #18** Programming by Navigation lets you navigate to
particular solutions to original underspecifications. Can you construct an
example specification and desired solution where `fill` will never give you the
desired solution but Programming by Navigation will? Generalizing a bit,
Programming by Navigation lets you reach any valid solution; in contrast, can
you characterize the class of programs that `fill` will return?

Whew! Here are some test cases for you to try out.

```python
spec = [({"in": 4}, 10), ({"in": 0}, 2)]
spec = [({"in": 3}, 9)]
spec = [({"in": i}, 3 * i) for i in range(10)]

pbn(spec)
```

With that, we've implemented in the essence of Programming by Navigation in
~50 lines of Python code! We started from standard program evaluation, ventured
through traditional program synthesis, and used both to implement a
nonempty-completion oracle for a step provider that satisfies Strong Soundness
and Strong Completeness.

I hope I've enticed you to think about some of the questions to ponder
throughout this post! Some of them are rather direct (_e.g._, #2, #14) but some
of them lead to wide-open research areas that I'm excited to work on (_e.g._,
#13, #17)!

What questions or thoughts do you have? I'd love to hear! Please do feel free
to email me at [justinlubin@berkeley.edu](mailto://justinlubin@berkeley.edu) to
chat anytime.

Bye for now!

Justin

July 2026

Berkeley, CA, USA

