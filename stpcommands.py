#!/usr/bin/python
# -*- coding: UTF-8 -*-

__author__ = "Rainy"


import copy
import subprocess


""" ---------------------------- The function for STP ---------------------------------- """


def setupQuery():
    """
    Adds the query and printing of counterexample to the stp stpfile.
    """
    command = ""
    command += "QUERY(FALSE);\n"
    command += "COUNTEREXAMPLE;\n"
    return command


def solver(solve_file):
    """
    :param solve_file:
    :return: "valid" for True; "invalid" for False
    """
    stp_parameters = ["stp", "--cryptominisat", "--thread", "1", "--CVC", solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.decode().replace("\r", "")[0:-1]
    print(res)
    if res == "Valid.":
        return True
    else:
        return False


""" -------------------------- The function for basic Operations ---------------------------------- """


def __equal(var1, var2):
    """
    :param var1: x1
    :param var2: x2
    :return: ASSERT(x1 = x2)
    """
    return "ASSERT({} = {});\n".format(var1, var2)


def __xor(var1, var2):
    """
    :param var1: x1
    :param var2: x2
    :return: (x1 ^ x2)
    """
    return "BVXOR({}, {})".format(var1, var2)


def __le(var1, var2):
    """
    :param var1: x1
    :param var2: x2
    :return: x1 < x2
    """
    return "ASSERT(BVLE({}, {}));\n".format(var1, var2)


def __ge(var1, var2):
    """
    :param var1: x1
    :param var2: x2
    :return: x1 > x2
    """
    return "ASSERT(BVGE({}, {}));\n".format(var1, var2)


def __lt(var1, var2):
    """
    :param var1: x1
    :param var2: x2
    :return: x1 =< x2
    """
    return "ASSERT(BVLT({}, {}));\n".format(var1, var2)


def __GT(var1, var2):
    """
    :param var1: x1
    :param var2: x2
    :return: x1 >= x2
    """
    return "ASSERT(BVGE({}, {}));\n".format(var1, var2)


""" -------------------------- The function for declaring variables ---------------------------------- """


def creatVariablesForSingle(var, index, size):
    """
    :param var: notion -> x,y,...
    :param index: round number -> r
    :param size: length of x -> l
    :return: [x_r_0, x_0_1, ... , x_0_(l-1)]
    """
    var1 = ["{}_{}_{}".format(var, index, j) for j in range(0, size)]
    return var1


def creatVariablesForMultiple(var, index, size, mul):
    """
    Applying to describe state propagation
    :param var: notion -> x,y,...
    :param index: round number -> r
    :param size: length of x -> l
    :param mul: the number of state -> m
    :return: [[P0_x_r_0, P0_x_0_1, ... , P0_x_0_(l-1)], ... , [P(m-1)_x_r_0, P(m-1)_x_0_1, ... , P(m-1)_x_0_(l-1)]
    """
    var1 = [["P{}_{}_{}_{}".format(m, var, index, i) for i in range(0, size)] for m in range(0, mul)]
    return var1


def getStringForVariables(variables, wordsize):
    """
    :param variables: [[x_0_0, ... , x_0_1], ... , [x_r_0, ... , x_r_1]]
    :param wordsize: length of x_i_j
    :return: x_0_0, ... , x_0_1: BITVECTOR(wordsize);
             ...
             x_r_0, ... , x_r_1: BITVECTOR(wordsize);
    """
    command = ""
    for var in variables:
        for i in range(0, len(var)):
            command += var[i] + ","
        command = command[:-1]
        command += ": BITVECTOR({0});\n".format(wordsize)
    return command


""" -------------------------- The function for asserting values for variables ---------------------------------- """


def __xorvalues(var1, var2, wordsize):
    """
    :param var1: variable -> x
    :param var2: value -> a
    :param wordsize: length of variable
    :return: (x ^ bin(a))
    """
    tmp = "0bin"
    for j in range(0, wordsize):
        tmp += "{}".format((var2 >> (wordsize - 1 - j)) & 0x1)
    return "BVXOR({}, {})".format(var1, tmp)


def assertValuesForVariable(var, value, wordsize):
    """
    :param var: a variable -> x
    :param value: a int value -> a
    :param wordsize: lenght of x
    :return: ASSERT(x = bin(a));
    """
    tmp = "0bin"
    for j in range(0, wordsize):
        tmp += "{}".format((value >> (wordsize-1-j)) & 0x1)
    return __equal(var, tmp)


""" ----------------------- The function for some basic opeartions applying to string ---------------------------- """


def getStringForNonZero(variables, wordsize):
    """
    Asserts that no all-zero characteristic is allowed
    :param variables: [x_0, x_1, ... , x_l]
    :param wordsize: length of x_0
    :return: x_0 | x_1 | .. | x_l != 0bin0
    """
    command = "ASSERT(NOT(("
    for var in variables:
        command += var + "|"

    command = command[:-1]
    command += ") = 0bin{}));\n".format("0" * wordsize)
    return command


def getStringOR(rin):
    """
    :param rin: [x_0, x_1, ... , x_l]
    :return: (x_0 | x_1 | ... | x_l)
    """
    rout = "{}".format(rin[0])
    for i in range(1, len(rin)):
        rout += "|{}".format(rin[i])
    return "({})".format(rout)


def getStringPermutation(varIN, perm):
    """
    :param varIN: a list -> X = [x_0, x_1, ... , x_l]
    :param perm:  a permutation -> h
    :return: h(X) = [x_h[0], x_h[0], ... , x_h[l]]
    """
    varOUT = ["" for i in range(0, len(varIN))]
    for i in range(0, len(varIN)):
        varOUT[i] = varIN[perm[i]]
    return varOUT


def getStringPlus(var, wordsize, size):
    """
    :param var: [x_0, x_1, ... , x_l]
    :param wordsize: length of x_0
    :param size: module add 2**n
    :return: (x_0 + x_1 + ... + x_l) mod 2**n
    """
    command = "BVPLUS({}".format(size)
    header = ""
    if wordsize < size:
        header += "0bin{}@".format("0" * (size-wordsize))

    for i in range(0, len(var)):
        command += ", {}".format(header+var[i])
    command += ")"
    return command


def assertValuesForString(var, values, wordsize):
    """
    :param var: a list of variable -> [x_0, x_1, ... , x_l]
    :param values: a set of int values -> [a_0, a_1, ... , a_l]
    :param wordsize: length of x_0
    :return: x_0 = bin(a_0); x_1 = bin(a_1); ... , x_l = bin(a_l);
    """
    command = ""
    for i in range(0, len(var)):
        command += assertValuesForVariable(var[i], values[i], wordsize)
    return command


def assertValuesForXorString(var1, var2, values, wordsize):
    """
    :param var1: a list of variable -> [x_0, x_1, ... , x_l]
    :param var2: a list of variable -> [y_0, y_1, ... , y_l]
    :param values: a set of int values -> [a_0, a_1, ... , a_l]
    :param wordsize: length of x_0
    :return: x_0 ^ y_0 = bin(a_0); x_1 ^ y_1 = bin(a_1); ... , x_l ^ y_1= bin(a_l);
    """
    command = ""
    for i in range(0, len(var1)):
        command += assertValuesForVariable(__xor(var1[i], var2[i]), values[i], wordsize)
    return command


def assertValuesLeForVariable(var, value, wordsize):
    """
    :param var: a variable -> x
    :param value: a int value -> a
    :param wordsize: lenght of x
    :return: ASSERT(x = bin(a));
    """
    tmp = "0bin"
    for j in range(0, wordsize):
        tmp += "{}".format((value >> (wordsize-1-j)) & 0x1)
    return __le(var, tmp)


""" ----------------------- The function for some basic operation of MixColumns Operation ------------------------ """


def __matrixMultiplyOperation(varIN, varOUT, matrix):
    """
    Mixcolumns operation for o-1 matrix
    :param varIN: input variable -> X
    :param varOUT: output variable -> Y
    :param matrix: 0-1 matrix
    :return: Y = M * X
    """
    # if mode == "MDS":
    #     matrix = formattingInput.__finite_matrix_2_bit_matrix(mat[0], mat[1])
    # elif mode == "AMDS":
    #     matrix = formattingInput.__word_zero_one_matrix_2_bit_matrix(mat[0], mat[1])
    # else:
    #     matrix = copy.deepcopy(mat)

    subcommand = ""
    for matRow in range(0, len(matrix)):
        varLIST = list()
        for matCol in range(0, len(matrix[0])):
            if matrix[matRow][matCol] == 1:
                varLIST.append(varIN[matCol])
        if len(varLIST) == 1:
            com = "{}".format(varLIST[0])
        elif len(varLIST) == 2:
            com = __xor(varLIST[1], varLIST[0])
        else:
            com = __xor(varLIST[1], varLIST[0])
            for m in range(2, len(varLIST)):
                com = __xor(varLIST[m], com)
        subcommand += __equal(varOUT[matRow], com)
    return subcommand


def getStringXor(var1, var2, var3):
    """
    String values Xor: Z = X ^ Y, where X = (x0, ... xn), Y = (y0, ... yn)
    """
    command = ""
    for i in range(0, len(var1)):
        command += __equal(var3[i], __xor(var1[i], var2[i]))
    return command


def stringToValue(List, size):
    Str = ""
    l = len(List) // size
    for i in range(0, l):
        for j in range(0, size):
            Str += "{}".format(List[i*size+j])
        Str += " "
    return Str


def listTostring(List, size):
    Str = ""
    l = len(List) // size
    for i in range(0, l):
        for j in range(0, size):
            Str += "{:x}".format(List[i*size+j]).zfill(size//4)
        Str += " "
    return Str


def parsingResultsForSingle(res, round_inf, blocksize, wordsize, size):
    res = res.split("\n")
    res = res[0:-1]
    values_dict = dict()
    for r in res:
        r = r.replace("ASSERT( ", "")
        r = r.replace(" );", "")
        if wordsize % 4 == 0:
            r = r.split(" = 0x")
        else:
            r = r.split(" = 0b")
        values_dict[r[0]] = r[1]

    command = ""
    for i in range(round_inf[0], round_inf[1]+1):
        varx = list(range(blocksize))
        for key, value in values_dict.items():
            if key.split("_")[0] == "x" and key.split("_")[1] == str(i):
                varx[int(key.split("_")[2])] = value
        command += "x{}: {}\n".format(i, stringToValue(varx, size))
    return command

