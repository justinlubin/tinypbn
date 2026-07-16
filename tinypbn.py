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


def satisfies(spec, sketch):
    return all(eval(env, sketch) == out for env, out in spec)


def size(sketch):
    if isinstance(sketch, tuple):
        return sum(map(size, sketch))
    return 1


def expand(sketch):
    if size(sketch) >= 5:
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


def fill(spec, sketch):
    worklist = [sketch]
    while worklist:
        candidate = worklist.pop(0)
        if satisfies(spec, candidate):
            return candidate
        worklist.extend(expand(candidate))


def nonempty_completion(spec, sketch):
    return fill(spec, sketch) is not None


def provide(spec, sketch):
    return [c for c in expand(sketch) if nonempty_completion(spec, c)]


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


spec = [({"in": 4}, 10), ({"in": 0}, 2)]
spec = [({"in": 3}, 9)]
spec = [({"in": i}, 3 * i) for i in range(10)]

pbn(spec)
