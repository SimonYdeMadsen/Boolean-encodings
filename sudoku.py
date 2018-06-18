# -*- coding: utf-8 -*-

import numpy as np
import re
import time
from common import *


def var(*args):
    assert len(args) == 3
    name = "X(%d,%d)=%d" % (args[0], args[1], args[2])
    return Var(name)



def read_file_into_matrix(file_name, format):
    rows = 0
    cols = 0

    if format == 1:

        with open(file_name, 'r') as f:
            for i, line in enumerate(f):
                if line[0] in ('\n', ' '):
                    break
                if i == 0:
                    cols = len(line.split(','))
                rows += 1

        shape = (rows, cols)
        m = np.zeros(shape, dtype=int)

        with open(file_name, 'r') as file:
            for i, line in enumerate(file):
                if line[0] in ('\n', ' '):
                    break
                line = line.split('\n')[0]
                line = line.split(',')

                m[i] = line
        return m
    if format == 2:

        with open(file_name, 'r') as file:
            last_line_was_newline = False
            for i, line in enumerate(file):
                if line[0] == '\n':
                    if last_line_was_newline == True:
                        break
                    last_line_was_newline = True
                    continue
                last_line_was_newline = False
                if i == 0:
                    cols = len(line.split('  '))
                rows += 1
        shape = (rows, cols)
        mat = [[" " for j in range(shape[1])] for i in range(shape[0])]
        i = 0
        with open(file_name, 'r') as file:
            last_line_was_newline = False
            for line in file:
                if line[0] == '\n':
                    if last_line_was_newline == True:
                        break
                    last_line_was_newline = True
                    continue
                last_line_was_newline = False

                line = line.split('\n')[0]
                line = line.split('  ')
                line = [0 if x.strip() == '*' else ord(x.strip()) if not x.strip().isdigit() else int(x)+1 for x in line ]
                line = [x-54 if x > 10 else x for x in line]

                mat[i] = line
                i += 1

        return mat


    if format == 3:

        with open(file_name, 'r') as f:
            for i, line in enumerate(f):
                if line[0] in ('\n', ' '):
                    break
                if i == 0:
                    if line[-2] == ' ':
                        line = line[:-2]
                    cols = len(line.split(' '))
                rows += 1

        shape = (rows, cols)
        m = np.zeros(shape, dtype=int)

        with open(file_name, 'r') as file:
            for i, line in enumerate(file):
                if line[0] in ('\n', ' '):
                    break
                line = line.split('\n')[0]
                if line[-1] == ' ':
                    line = line[:-1]
                line = line.split(' ')
                print line
                m[i] = line
        return m


size = 25
input_format = 1
if size < 16: input_format = 1
elif size == 16: input_format = 2
elif size == 25: input_format = 3

m = read_file_into_matrix("sudoku-input-%dx%d.txt" % (size, size), input_format)

print("Input:")
for x in m:
    print x
print("\n\n")

board_range = list(range(0, len(m[0])))
number_range = [x+1 for x in board_range]


var2int = {}
num_vars = 0
clauses = []




computation_start_time = time.clock()

fs = []
at_most_one_per_box = []
sqrt_n = int(np.sqrt(len(m[0])))
prev_box_i, prev_box_j = -1, -1
for i, row in enumerate(m):
    #print("row: " + str(row))
    for j, val in enumerate(row):

        offset_i = i / sqrt_n * sqrt_n
        box_i_range = range(offset_i, offset_i + sqrt_n)

        offset_j = j / sqrt_n * sqrt_n
        box_j_range = range(offset_j, offset_j + sqrt_n)

        if offset_i != prev_box_i or offset_j != prev_box_j:

            box_impl = [andify([Impl(var(i, j, k),
                         andify([Not(var(x, y, k)) for x in box_i_range for y in box_j_range
                             if not (x == i and y == j)]))]) for k in number_range]
            at_most_one_per_box.append(andify(box_impl))

        prev_box_i, prev_box_j = offset_i, offset_j

        if val != 0:
            # Handle the initial state of the game board

            # This field must have this value
            field_init = [var(i, j, val)]

            # No other variables at this field can assume this value
            field_unique = [andify([Not(var(i, j, k)) if k != val else var(i, j, k) for k in number_range])]
            # print("field: "+ str(field))

            # Initial uniqueness constraint on row
            row = [andify([Not(var(i, y, val)) for y in board_range if y != j])]
            # print("row: "+str(row))

            # Initial uniqueness constraint on column
            col = [andify([Not(var(x, j, val)) for x in board_range if x != i])]

            # Initial uniqueness constraint on box
            box = [andify([Not(var(x, y, val)) for x in box_i_range for y in box_j_range if not (x == i and y == j)])]
            # print("box: " + str(box))

            fs.extend(field_init)
            fs.extend(field_unique)
            fs.extend(row)
            fs.extend(col)
            fs.extend(box)



at_least_one_per_field = [orify([var(x, y, k) for k in number_range]) for x in board_range for y in board_range]


at_most_one_per_row = [andify([Impl(var(x, y, k), Not(var(x, z, k)))]) for k in number_range for x in board_range for y in board_range
                       for z in board_range if y != z]

at_most_one_per_column = [andify([Impl(var(x, y, k), Not(var(z, y, k)))]) for k in number_range for x in board_range for y in board_range
                          for z in board_range if x != z]


print "at_least_one_per_field has length %d." % len(at_least_one_per_field)
print "at_most_one_per_row has length %d." % len(at_most_one_per_row)
print "at_most_one_per_column has length %d." % len(at_most_one_per_column)
print "at_most_one_per_box has length %d." % len(at_most_one_per_box)


fs.extend(at_least_one_per_field)
fs.extend(at_most_one_per_row)
fs.extend(at_most_one_per_column)
fs.extend(at_most_one_per_box)


clauses = list(numberfy(tseitin(andify(fs))))

output_string = to_dimacs(clauses, Var.count)

out_file = open("sudoku-output.txt", "w")
out_file.write(output_string)
out_file.close()

computation_end_time = time.clock()

view_satisfiable_assignment = True
visualization_start_time = time.clock()
if view_satisfiable_assignment:
    id2name = {v: k for k, v in Var.name2id.iteritems()} #Create an inverted map

    display_matrix = np.zeros((len(m), len(m[0])), dtype=int)

    satisfiable = ""
    with open('lingeling-sudoku-output.txt', 'r') as in_file:
        for line in in_file:
            if line[0] == 's':
                satisfiable = line[2:]
            if line[0] != 'v':
                continue
            line = line.split('v ')[1]
            string = line.split(' ')
            for id_str in string:
                if id_str[0] == '-':
                    continue
                    #string = string[1:]
                    #positive = False
                if int(id_str) not in id2name.keys():
                    #If fresh variable
                    continue
                variable = id2name[int(id_str)]
                variables = re.split('X\(|,|\)=', variable)[1:]
                variables = list(map(int, variables))
                x, y, k = variables
                #print x, y, k
                display_matrix[x, y] = k



    print(display_matrix)
    print "satisfiable?", satisfiable

visualization_end_time = time.clock()

print "clauses: ", len(clauses)
print "variables: ", Var.count

print "Computation time: %d." % (computation_end_time - computation_start_time)
print "Visualization time: %d." % (visualization_end_time - visualization_start_time)