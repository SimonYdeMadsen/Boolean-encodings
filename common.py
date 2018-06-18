from enclib import *



def andify(fs):
    if not fs:
        raise ValueError("Andify called with an empty list.")
    if len(fs) == 1:
        return fs[0]
    return And(andify(fs[:len(fs) // 2]), andify(fs[len(fs) // 2:]))


def orify(fs):
    if not fs:
        raise ValueError("Orify called with an empty list.")
    if len(fs) == 1:
        return fs[0]
    return Or(orify(fs[:len(fs) // 2]), orify(fs[len(fs) // 2:]))


def dimacsify(clause):
    return " ".join(map(str, list(clause)))


def to_dimacs(clauses_param, num_vars_param):
    num_clauses = len(list(clauses_param))

    print "p cnf %d %d" % (num_vars_param, num_clauses)
    dimacs_clauses = " 0\n".join(map(dimacsify, clauses_param)) + " 0"
    return "p cnf %d %d\n%s" % (num_vars_param, num_clauses, dimacs_clauses)





def numberfy(cs):
    ret = [[literal.id if isinstance(literal,Var) else -literal.fs[0].id for literal in clause ] for clause in cs]
    #ret = map(lambda c:map(lambda l:l.id if isinstance(l,Var) else -l.fs[0].id,c),cs)
    return ret
