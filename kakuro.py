#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import numpy as np
from common import *


def bin_var(field, k):
    name = "B{%d,%d}:%d" % (field[0], field[1], k)
    return Var(name)


def carry_var(field_1, field_2, k):
    #This variable represents the k'th carry-bit when adding num_1 and num_2
    name = "C{%s,%s}:%d" % (field_1, field_2, k)
    return Var(name)


def sum_var(field_1, field_2, k):
    #This variable represents the k'th bit in the sum of the addition of num_1 and num_2
    name = "S{%s,%s}:%d" % (field_1, field_2, k)
    return Var(name)





def read_file_into_matrix_old(file_name):

    rows = 0
    cols = 0
    with open(file_name, 'r') as f:
        for i, line in enumerate(f):
            if line[0] in ('\n', ' '):
                break
            if i == 0:
                cols = len(line.split(','))
            rows += 1

    shape = (rows, cols)
    mat = np.zeros(shape, dtype=int)
    with open(file_name, 'r') as f:
        for i, line in enumerate(f):
            if line[0] in ('\n', ' '):
                break
            print "line:",line
            line = line.split('\n')[0]
            line = line.split(',')
            line = ["-1" if line[x] == "XX" else line[x] for x, field in enumerate(line)]
            try:
                mat[i] = line
            except ValueError:
                print "ValueError: ", line
                print "Failed to coerce line into matrix."
                exit(1)

    return mat, shape


def read_file_into_matrix(file_name):

    rows = 0
    cols = 0
    with open(file_name, 'r') as f:
        for i, line in enumerate(f):
            if line[0] == '\n':
                break
            if i == 0:
                cols = len(line.split('|'))
            rows += 1

    shape = (rows, cols)

    mat = [[" " for j in range(shape[1])] for i in range(shape[0])]

    with open(file_name, 'r') as f:
        for i, line in enumerate(f):
            if line[0] == '\n':
                break
            line = line.split('\n')[0]
            line = line.replace("\\", "_")
            line = line.split('|')

            try:
                mat[i] = line
            except ValueError:
                print "ValueError: ", line
                print "Failed to coerce line into matrix."
                exit(1)

    return mat, shape


DEBUG = False
use_new_input_format = True
file_name = 'kakuro-input-12x12-hard.txt'
invalid_field_indicator = "0_0"
empty_field_indicator = "0"


computation_start_time = time.clock()

if use_new_input_format:
    m, shape = read_file_into_matrix(file_name)
else:
    m, shape = read_file_into_matrix_old(file_name)


#if DEBUG:
print("Input:")
for x in m:
    print x

#Remove any whitespace
m = [[m[x][y].replace(" ", "") for y in range(shape[1])] for x in range(shape[0])]



#field_max is the greatest number a non-sum field can assume
field_max = 9

#sum_max is the greatest number a sum can assume
sum_max = sum(range(1, field_max + 1))
print "sum_max: ", sum_max

#digits is the length of the binary numbers
digits = sum_max.bit_length()


print("board shape: %s" % (shape,))
print("\n")


number_range = list(range(1, field_max + 1))

#Initialize arrays
fs = []
carries_from_add = []
sums_from_add = []
equalities = []



def create_sum_dicts(m, shape):
    empty_fields = []
    row_dict = {}
    col_dict = {}
    for i in range(shape[0]):
        for j in range(shape[1]):
            if m[i][j] == invalid_field_indicator:
                continue

            if m[i][j] == empty_field_indicator:
                empty_fields.append((i, j))

            else:
                down, right = [int(x) for x in m[i][j].split('_')]

                assert down <= sum_max and right <= sum_max, "Invalid sum."

                if right:
                    row_dict[(i, j), right] = []
                    j_temp = j
                    try:
                        while m[i][j_temp + 1] == "0":
                            j_temp += 1
                            row_dict[(i, j), right].append((i, j_temp))
                    except IndexError:
                        pass

                if down:
                    col_dict[(i, j), down] = []
                    i_temp = i
                    try:
                        while m[i_temp + 1][j] == "0":
                            i_temp += 1
                            col_dict[(i, j), down].append((i_temp, j))
                    except IndexError:
                        pass
    return empty_fields, col_dict, row_dict


empty_fields, col_sum_dict, row_sum_dict = create_sum_dicts(m, shape)



def pretty_print_dict(m, dictie):
    for x in dictie:
        if dictie[x]:
            string = "%s = %s has list " % (x[0], x[1])
            string += ", ".join([str(y) for y in dictie[x]])
            assert len(dictie[x]) >= 1, "Program set to ignore sum of length 1."
            print string
    print ""

if DEBUG:
    print "\n row_sum_dict: "
    pretty_print_dict(m, row_sum_dict)
    print "\n col_sum_dict: "
    pretty_print_dict(m, col_sum_dict)



def dict_has_no_singletons(dictie):
    return all([len(dictie[x]) > 1 for  x in dictie if dictie[x]])

assert dict_has_no_singletons(col_sum_dict) and  dict_has_no_singletons(row_sum_dict), "A dict contains a list of length 1."


def int_to_binary_array(number,digits):
    return list(map(int, format(number, "0" + str(digits)+"b")[::-1]))


def int_to_binary_vars(number, field, digits):
    assert len(field) == 2

    bin_digits = int_to_binary_array(number,digits)

    bin_vars = [bin_var(field, b[0]) if b[1] else Not(bin_var(field, b[0])) for b in enumerate(bin_digits)]
    return andify(bin_vars)



at_least_one_per_empty_field = [orify([int_to_binary_vars(k, field, digits) for k in number_range]) for field in
                                empty_fields]


at_most_one_per_row = [andify([Impl(int_to_binary_vars(num, field, digits),
                                    Not(int_to_binary_vars(num, other_field, digits)))
                               for num in number_range for field in row_sum_dict[sum_field]
                               for other_field in row_sum_dict[sum_field] if other_field != field])
                       for sum_field in row_sum_dict if row_sum_dict[sum_field] and len(row_sum_dict[sum_field]) > 1]


at_most_one_per_col = [andify([Impl(int_to_binary_vars(num, field, digits),
                                    Not(int_to_binary_vars(num, other_field, digits)))
                               for num in number_range for field in col_sum_dict[sum_field]
                               for other_field in col_sum_dict[sum_field] if other_field != field])
                       for sum_field in col_sum_dict if col_sum_dict[sum_field] and len(col_sum_dict[sum_field]) > 1]




def xor2(x, x_field, y, y_field, x_is_sum = False):
    #if is_sum is True, the x,x_field argument must contain the parameters for a bin_sum() object.
    bin_x = 0
    if x_is_sum:
        bin_x = sum_var(x_field[0], x_field[1], x)
    else:
        bin_x = bin_var(x_field, x)
    bin_y = bin_var(y_field, y)
    return Or(And(bin_x, Not(bin_y)), And(bin_y, Not(bin_x)))



def xor3(x, x_field, y, y_field, carry, x_is_sum=False):
    #x^y^c OR x ^ !y ^ !c OR y ^ !x ^ !c OR c ^ !y ^ !x
    #carry is a 3-tuple containing the integer x,y and a position
    assert len(carry) == 3

    bin_x = 0
    if x_is_sum:
        bin_x = sum_var(x_field[0], x_field[1], x)
    else:
        bin_x = bin_var(x_field, x)

    bin_y = bin_var(y_field, y)
    bin_c = carry_var(carry[0], carry[1], carry[2])

    all_expr = andify([bin_x, bin_y, bin_c])

    x_expr = andify([bin_x, Not(bin_y), Not(bin_c)])
    y_expr = andify([bin_y, Not(bin_x), Not(bin_c)])
    c_expr = andify([bin_c, Not(bin_x), Not(bin_y)])

    return orify([all_expr, x_expr, y_expr, c_expr])


def add_fields(n, x_field, y_field):

    if n == 1:

        bin_x = bin_var(x_field, 0)
        bin_y = bin_var(y_field, 0)
        bin_carry = carry_var(x_field, y_field, 1)
        #xor(x,y) and  x^y <=> c
        base_case = [[xor2(0, x_field, 0, y_field)],
                        [And(Impl(And(bin_x, bin_y), bin_carry), Impl(bin_carry, And(bin_x, bin_y)))]]
        if DEBUG:
            print "base_case: ", base_case
        return base_case

    c = add_fields(n-1, x_field, y_field)


    current_bit = xor3(n-1, x_field, n-1, y_field, (x_field, y_field, n-1))


    bin_x = bin_var(x_field, n-1)
    bin_y = bin_var(y_field, n-1)
    bin_carry = carry_var(x_field, y_field, n-1)

    next_carry = orify([And(bin_x, bin_y), And(bin_x, bin_carry), And(bin_y, bin_carry)])
    next_carry_var = carry_var(x_field, y_field, n)

    # next_carry <=> next_carry_var
    next_carry_expr = And(Impl(next_carry, next_carry_var), Impl(next_carry_var, next_carry))


    c[0].extend([current_bit])
    c[1].extend([next_carry_expr])
    if DEBUG:
        print "-----------------"
        print "bit %d (xor3) should be based on carry %d:" % (n-1, n-1), [current_bit]
        print "carry %d:" % n, [next_carry_expr]
        print "^ iter:", n - 1

    return c


def add_sum_and_field(n, last_fields, y_field):

    if n == 1:

        bin_x = sum_var(last_fields[0], last_fields[1], 0)
        bin_y = bin_var(y_field, 0)
        bin_carry = carry_var(last_fields[1], y_field, 1)
        #xor(x,y) and  x^y <=> c
        base_case = [[xor2(0, last_fields, 0, y_field, x_is_sum = True)],
                        [And(Impl(And(bin_x, bin_y), bin_carry), Impl(bin_carry, And(bin_x, bin_y)))]]
        if DEBUG:
            print "base_case: ", base_case
        return base_case

    c = add_sum_and_field(n-1, last_fields, y_field)


    current_bit = xor3(n-1, last_fields, n-1, y_field, (last_fields[1], y_field, n-1), x_is_sum = True)

    bin_sum = sum_var(last_fields[0], last_fields[1], n-1)
    bin_y = bin_var(y_field, n-1)
    bin_carry = carry_var(last_fields[1], y_field, n-1)

    next_carry = orify([And(bin_sum, bin_y), And(bin_sum, bin_carry), And(bin_y, bin_carry)])
    next_carry_var = carry_var(last_fields[1], y_field, n)

    # next_carry <=> next_carry_var
    next_carry_expr = And(Impl(next_carry, next_carry_var), Impl(next_carry_var, next_carry))


    c[0].extend([current_bit])
    c[1].extend([next_carry_expr])
    if DEBUG:
        print "-----------------"
        print "bit %d (xor3) should be based on carry %d:" % (n-1, n-1), [current_bit]
        print "carry %d:" % n, [next_carry_expr]
        print "^ iter:", n - 1

    return c





def assign_results_to_vars(sum_clauses, field_x, field_y):
    sum_variables = []
    assignments = []
    for i, clause in enumerate(sum_clauses):
        sum_variable = sum_var(field_x, field_y, i)
        if DEBUG:
            print "sum %d:" % i, sum_variable, "<=>", clause
        assignments.extend([And(Impl(sum_variable, clause), Impl(clause, sum_variable))])
        sum_variables.append(sum_variable)

    return assignments, sum_variables






def add_dict_fields(dictie):

    for sum_field in dictie:
        if not dictie[sum_field]:
            continue

        if DEBUG:
            print "sum_field:", sum_field


        previous_fields = ()
        #Loop from item 1, handeling item 0 in the first iteration
        for i in range(1, len(dictie[sum_field])):

            field_i = dictie[sum_field][i]
            field_i_minus_one = dictie[sum_field][i-1]

            result_from_add = []
            if i == 1:
                result_from_add = add_fields(digits, field_i_minus_one, field_i)
            else:
                result_from_add = add_sum_and_field(digits, previous_fields, field_i)

            carry_assignments = result_from_add[1]
            add_bit_clauses = result_from_add[0]

            sum_assignment, sum_variables = [], []

            sum_assignment, sum_variables = assign_results_to_vars(add_bit_clauses, field_i_minus_one, field_i)


            #print "sum_assignment:", sum_assignment
            #print "carry assignemnts:", carry_assignments

            carries_from_add.extend(carry_assignments)
            sums_from_add.extend(sum_assignment)



            last_iteration = i+1 == len(dictie[sum_field])
            if not last_iteration:
                previous_fields = (field_i_minus_one, field_i)
            else:

                sum_field_value = sum_field[1]
                assert sum_field_value <= sum_max, "sum_field_value (%d) exceeds sum_max (%d) " % (sum_field_value, sum_max)
                bin_sum = int_to_binary_array(sum_field_value, digits)
                equality_expr = andify([sum_variables[i] if bin_sum[i] else Not(sum_variables[i]) for i in range(len(bin_sum))])
                equalities.extend([equality_expr])


            if DEBUG:
                if i < 2: print "\n\n\nNext two fields\n----------------"

        if DEBUG:
            print "----------------------------------"
            print "field %s = %d done" % (sum_field[0], sum_field[1])
            print "----------------------------------"




add_dict_fields(row_sum_dict)

add_dict_fields(col_sum_dict)

fs.extend(at_least_one_per_empty_field)
fs.extend(at_most_one_per_row)
fs.extend(at_most_one_per_col)

fs.extend(carries_from_add)
fs.extend(sums_from_add)
fs.extend(equalities)


if DEBUG:
    print "equalities: "
    for x in equalities:
        print x


clauses = numberfy(tseitin(andify(fs)))

output_string = to_dimacs(clauses, Var.count)
computation_end_time = time.clock()
io_start_time = time.clock()
out_file = open("kakuro-output.txt", "w")
out_file.write(output_string)
out_file.close()
io_end_time = time.clock()



print "number of variables:", Var.count
print "number of clauses: ", len(clauses)

print "digits:", digits
print "field_max:", field_max
print "actual variables:", len(Var.name2id)
print "expected variables:", digits * len(empty_fields)



print "at_least_one_per_empty_field has %d clauses." % len(at_least_one_per_empty_field)
print "at_most_one_per_row has %d clauses." % len(at_most_one_per_row)
print "at_most_one_per_col has %d clauses." % len(at_most_one_per_col)
print "carries_from_add has %d clauses." % len(carries_from_add)
print "sums_from_add has %d clauses." % len(sums_from_add)
print "equalities has %d clauses." % len(equalities)



id2name = {v: k for k, v in Var.name2id.iteritems()} #Create the inverted dict for visualization

view_satisfiable_assignment = True

visualization_start_time = time.clock()

if view_satisfiable_assignment:

    strings = []
    satisfiable = ""

    binary_matrix = [[["0" for x in range(digits)] for j in range(shape[1])] for i in range(shape[0])]


    with open('lingeling-kakuro-output.txt', 'r') as in_file:
        for line in in_file:
            if line[0] == 's':
                satisfiable = line[2:]
            if line[0] != 'v':
                #print "Line starts with: ", line[0]
                continue
            line = line.split('v ')[1]
            strings.extend(line.split(' '))

    num_sum_vars = 0
    for id_str in strings:
        if id_str[0] == '-':
            #Ignore false variables
            continue
        if int(id_str) not in id2name.keys():
            #Ignore fresh variables
            continue
        var_name = id2name[int(id_str)]
        if DEBUG:
            print "variable_name: ", var_name
        if var_name[0] == 'B':
            var_num_array = re.split('\w{|,|}:', var_name)[1:]
            var_num_array = list(map(int, var_num_array))
            x, y, k = var_num_array
            binary_matrix[x][y][k] = "1"
        elif var_name[0] == 'S':

            num_sum_vars += 1
            if use_new_input_format: continue

            tuples = var_name.split('(')[0:3]
            tuples = [x.split(')')[0] for x in tuples[1:3]]

            field_1 = tuples[0].split(',')
            field_1 = tuple([int(x) for x in field_1])

            field_2 = tuples[1].split(',')
            field_2 = tuple([int(x) for x in field_2])

            sum_bit = int(var_name.split(':')[1])

            sum_direction = np.subtract(field_1, field_2)
            sum_down = True if sum_direction[1] == 0 else False
            sum_right = True if sum_direction[0] == 0 else False

            if sum_down:
                try:
                    if m[field_2[0]+1][field_2[1]] == "0":
                        #not a real sum
                        continue
                except IndexError:
                    pass
                #Modify relevant field above
                offset = 1
                print "sum_down"
                while m[field_1[0]-offset][field_1[1]] == "0":
                    #Find field to modify
                    offset += 1
                binary_matrix[field_1[0] - offset][field_1[1]][sum_bit] = "1"

            elif sum_right:
                try:
                    if m[field_2[0]][field_2[1]+1] == 0:
                        #Not a final sum
                        continue
                except IndexError:
                    pass
                #Modify relevant field to the left
                offset = 1
                while m[field_1[0]][field_1[1]-offset] == 0:
                    #Find the field to modify
                    offset += 1

                binary_matrix[field_1[0]][field_1[1] - offset][sum_bit] = "1"


    # print "(binary) binary_matrix: "
    # for x in binary_matrix:
    #     print x

    #display_matrix = np.zeros(shape, dtype=int)
    display_matrix = m
    print "num_sum_vars: ", num_sum_vars
    #Create an integer display matrix from the binary one
    for row in range(len(binary_matrix)):
        for col in range(len(binary_matrix[row])):
            if display_matrix[row][col].strip() == "0":
                display_matrix[row][col] = str(int("".join(binary_matrix[row][col][::-1]), 2))
            display_matrix[row][col] = display_matrix[row][col].center(5)

    print "(integer) display_matrix: "
    for x in display_matrix:
        print x


    if satisfiable[0:2] == "UN":
        print "------------------------------------------------------------------"
        print "------------------------------------------------------------------"
        print "------------------------------------------------------------------"
        print "------------------------------------------------------------------"
    print "satisfiable? ", satisfiable
    if satisfiable[0:2] == "UN":
        print "------------------------------------------------------------------"
        print "------------------------------------------------------------------"
        print "------------------------------------------------------------------"
        print "------------------------------------------------------------------"

visualization_end_time = time.clock()

print "Computation time: %d. " % (computation_end_time - computation_start_time)
print "IO time: %d." % (io_end_time - io_start_time)
print "Visualization time: %d." % (visualization_end_time - visualization_start_time)

# for x in sums_from_add:
#     for y in x.fs:
#         for z in y.fs:
#             print z
#             if z != y.fs[-1]:
#                 print y.__class__.__name__
#         if y != x.fs[-1]:
#             print x.__class__.__name__
#
#     print "\n"

# for x in carries_from_add:
#     for y in x.fs:
#         for z in y.fs:
#             print z
#             if z != y.fs[-1]:
#                 print y.__class__.__name__
#         if y != x.fs[-1]:
#             print x.__class__.__name__
#
#     print "\n"

# for x in at_least_one_per_empty_field:
#     for y in x.fs:
#         for z in y.fs:
#             for d in z.fs:
#
#                 print d
#                 if d != z.fs[-1]:
#                     print z.__class__.__name__
#
#         if y != x.fs[-1]:
#             print x.__class__.__name__
#     print ""

