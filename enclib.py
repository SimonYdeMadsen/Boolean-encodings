#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Var():
    count = 0
    name2id = {}

    def __init__(self, name, fresh=False):
        self.name = name
        if not fresh and name in Var.name2id:
            self.id = Var.name2id[name]
        else:
            Var.count += 1
            self.id = Var.count
            if not fresh:
                self.name2id[name] = self.id

    def __repr__(self):
        return "%s" % repr(self.name)

    def __neg__(self):
        var = Var(self.name)
        var.positive = not self.positive
        return var

    def tseitin(self):
        return self, []


class Binary():
    def tseitin(self):
        assert 1 <= len(self.fs) <= 2
        fresh = Var("_", fresh=True)

        x, cs = self.fs[0].tseitin()
        y = None
        if len(self.fs) == 2:
            y, ds = self.fs[1].tseitin()
            cs.extend(ds)
        cs.extend(self.rule(x, y, fresh))
        return fresh, cs


class And(Binary):
    def __init__(self, *fs):
        self.fs = fs

    def __repr__(self):
        return "(%s)" % " ^ ".join(map(repr, self.fs))

    def rule(self, x, y, fresh):
        return [[Not(x), Not(y), fresh], [Not(fresh), x], [Not(fresh), y]]


class Or(Binary):
    def __init__(self, *fs):
        self.fs = fs

    def __repr__(self):
        return "(%s)" % " ∨ ".join(map(repr, self.fs))

    def rule(self, x, y, fresh):
        return [[Not(x), fresh], [Not(y), fresh], [Not(fresh), x, y]]


class Impl(Binary):
    def __init__(self, f, g):
        self.fs = [f, g]

    def __repr__(self):
        return "(%s)" % " => ".join(map(repr, self.fs))

    def rule(self, x, y, fresh):
        return [[x, fresh], [Not(y), fresh], [Not(fresh), Not(x), y]]


class Not(Binary):
    def __init__(self, f):
        self.fs = [f]

    def __repr__(self):
        return "Not(%s)" % repr(self.fs[0])

    def rule(self, x, y, fresh):
        return [[x, fresh], [Not(x), Not(fresh)]]



def tseitin(f):
    x, cs = f.tseitin()
    cs.append([x])
    return cs