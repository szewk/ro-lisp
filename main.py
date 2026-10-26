from __future__ import annotations

from collections.abc import Iterator
from itertools import chain
from sys import exit, setrecursionlimit

setrecursionlimit(1000000)


List = list


class Symbol:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def __repr__(self) -> str:
        return self.symbol

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Symbol):
            return self.symbol == value.symbol
        return False


class EmptyList:
    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return "()"

    def __eq__(self, value: object) -> bool:
        return isinstance(value, EmptyList)


EMPTYLIST = EmptyList()


class LinkedList:
    def __init__(
        self, head: Expression, tail: LinkedList | EmptyList = EMPTYLIST
    ) -> None:
        self.head: Expression = head
        self.tail: Expression = tail

    def __repr__(self) -> str:
        if self.tail is not EMPTYLIST:
            return f"({self.head} {repr(self.tail)[1:-1]})"
        return f"({self.head})"


Atom = Symbol | EmptyList

Expression = LinkedList | Atom

QUOTE = Symbol("quote")
ATOM = Symbol("atom")
EQ = Symbol("eq")
CAR = Symbol("car")
CDR = Symbol("cdr")
CONS = Symbol("cons")
COND = Symbol("cond")
LAMBDA = Symbol("lambda")
LABEL = Symbol("label")
T = Symbol("t")


def assoc(x: Atom, y: LinkedList) -> Expression:
    if y.head.head == x:
        return y.head.tail.head
    return assoc(x, y.tail)


def evcon(c: LinkedList, env: LinkedList) -> Expression:
    if eval(c.head.head, env) == T:
        return eval(c.head.tail.head, env)
    return evcon(c.tail, env)


def evlis(m: LinkedList | EmptyList, env: LinkedList) -> Expression:
    if m == EMPTYLIST:
        return EMPTYLIST
    return LinkedList(eval(m.head, env), evlis(m.tail, env))


def list(*exps: Expression) -> LinkedList:
    if not exps:
        return EMPTYLIST
    return LinkedList(exps[0], list(*exps[1:]))


def append(x: LinkedList, y: LinkedList) -> LinkedList:
    if x == EMPTYLIST:
        return y
    return LinkedList(x.head, append(x.tail, y))


def pair(x: Expression, y: Expression) -> LinkedList | EmptyList:
    if x == EMPTYLIST and y == EMPTYLIST:
        return EMPTYLIST
    elif not isinstance(x, Atom) and not isinstance(y, Atom):
        return LinkedList(list(x.head, y.head), pair(x.tail, y.tail))


def eval(exp: Expression, env: LinkedList) -> Expression:
    if isinstance(exp, Atom):
        return assoc(exp, env)
    elif isinstance(exp.head, Atom):
        if exp.head == QUOTE:
            return exp.tail.head

        elif exp.head == ATOM:
            return T if isinstance(eval(exp.tail.head, env), Atom) else EMPTYLIST

        elif exp.head == EQ:
            return (
                T
                if eval(exp.tail.head, env) == eval(exp.tail.tail.head, env)
                else EMPTYLIST
            )

        elif exp.head == CAR:
            return eval(exp.tail.head, env).head

        elif exp.head == CDR:
            return eval(exp.tail.head, env).tail

        elif exp.head == CONS:
            return LinkedList(eval(exp.tail.head, env), eval(exp.tail.tail.head, env))

        elif exp.head == COND:
            return evcon(exp.tail, env)

        else:
            return eval(LinkedList(assoc(exp.head, env), exp.tail), env)

    elif exp.head.head == LABEL:
        return eval(
            LinkedList(exp.head.tail.tail.head, exp.tail),
            LinkedList(list(exp.head.tail.head, exp.head), env),
        )
    elif exp.head.head == LAMBDA:
        return eval(
            exp.head.tail.tail.head,
            append(pair(exp.head.tail.head, evlis(exp.tail, env)), env),
        )


def tokenize(text: str) -> Iterator[str]:
    i, n = 0, len(text)
    while i < n:
        char = text[i]
        if char in "()'":
            yield char
            i += 1
            continue
        elif char.isspace():
            i += 1
        else:
            j = i
            while j < n and text[j] not in "()'" and not text[j].isspace():
                j += 1
            yield text[i:j]
            i = j


def parse(tokens: Iterator[str]) -> Expression:
    token = next(tokens)
    if token == "'":
        return list(QUOTE, parse(tokens))
    if token == "(":
        items: List[Expression] = []
        for token in tokens:
            if token in "('":
                items.append(parse(chain([token], tokens)))
            elif token == ")":
                break
            else:
                items.append(Symbol(token))
        return list(*items)

    return Symbol(token)


def read(text: str) -> Expression:
    return parse(tokenize(text))


env = list(list(EMPTYLIST, EMPTYLIST), list(T, T))


def greet() -> None:
    print("\nRo-LISP: Minimal LISP interpreter\n\n,h for help\n,q to exit\n")


def help() -> None:
    greet()
    with open("man") as man:
        print(man.read())


def position(lines: str) -> str:
    balanced = 0
    first_word = True
    i = len(lines) - 1
    cnt = 0
    curline = lines.count("\n")
    while True:
        if lines[i] == ")":
            balanced += 1
            first_word = False
        elif lines[i] == "(":
            balanced -= 1
            if lines[i - 1] == "'":
                first_word = True
        elif lines[i].isspace():
            if lines[i] == "\n":
                cnt = -1
                curline -= 1
            first_word = False
        cnt += 1
        if balanced == 0 and not first_word:
            if lines[i].isspace():
                cnt -= 1
            break
        i -= 1
    return " " * (len(lines.split("\n")[curline].rstrip()) - cnt)


def repl() -> None:
    lines = []
    try:
        line = input(">>> ")
    except KeyboardInterrupt:
        print()
        repl()

    balanced = 0

    while True:
        if line.strip() == ",q":
            exit(0)

        if line.strip() == ",h":
            help()
            repl()

        lines.append(line)
        balanced += line.count("(") - line.count(")")

        if balanced == 0:
            break

        try:
            pos = position("\n".join(lines))
            line = input("... " + pos)
            line = pos + line
        except KeyboardInterrupt:
            print()
            lines = []
            break

    inp = "\n".join(lines)
    if inp:
        print(str(eval(read(inp), env)))
    repl()


if __name__ == "__main__":
    greet()
    repl()
