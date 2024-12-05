#!/usr/bin/python
# -*- coding: UTF-8 -*-

__author__ = "Rainy"
"""
some operations used in differential analysis of block ciphers.
"""


import stpcommands as stp
import numpy as np
import math


""" ---------------------------- The funtion for SubCell Operation ----------------------------------- """


def computeDDT(sbox, size):
    """
    Computer the DDT for sbox with any size
    :param sbox: a list of sbox [0x2, 0x4, ... , 0xf]
    :param size: size of sbox
    :return: ddt
    """
    DDT = [[0 for i in range(0, 2**size)] for j in range(0, 2**size)]
    for i in range(0, 2**size):
        for j in range(0, 2**size):
            DDT[i ^ j][sbox[i] ^ sbox[j]] += 1
    return DDT


def __readDDT(sin, sout, DDT, size):
    """
    read the look-up table of DDT in CVC format for any sbox
    :param sin: the input variables of sbox
    :param sout: the output variables of sbox
    :param DDT: DDT
    :param size: sbox size
    :return: the statement of looking up the differential distribute table
    """
    subcommand = ""
    if size == 4:
        subcommand = "0x0"
        for row in range(0, 2**size):
            for col in range(0, 2**size):
                if DDT[row][col] != 0:
                    subcommand = "(IF {} = 0x{:0>x} AND {} = 0x{:0>x} THEN 0x{:0>x} ELSE {} ENDIF)".format(
                        sin, row, sout, col, DDT[row][col], subcommand
                    )
    elif size == 8:
        subcommand = "0x00"
        for row in range(0, 2**size):
            for col in range(0, 2**size):
                if DDT[row][col] != 0:
                    subcommand = "(IF {} = 0x{:0>2x} AND {} = 0x{:0>2x} THEN 0x{:0>2x} ELSE {} ENDIF)".format(
                        sin, row, sout, col, DDT[row][col], subcommand
                    )
    else:
        print("Sbox operation: The sbox size is invalid.")
    return subcommand


def __readDDTForSpecialSbox(sin, sout, DDT, size):
    """
    read the look-up table of DDT in CVC format for sbox whose log(s[x][y], 2) is integer
    :param sin: the input variables of sbox
    :param sout: the output variables of sbox
    :param DDT: DDT
    :param size: sbox size
    :return: the statement of looking up the differential distribute table
    """
    subcommand = ""
    if size == 4:
        subcommand = "0x4"
        for row in range(0, 2**size):
            for col in range(0, 2**size):
                if DDT[row][col] != 0:
                    subcommand = "(IF {} = 0x{:0>x} AND {} = 0x{:0>x} THEN 0x{:0>x} ELSE {} ENDIF)".format(
                        sin, row, sout, col, size - int(math.log2(DDT[row][col])), subcommand
                    )
    elif size == 8:
        subcommand = "0x08"
        for row in range(0, 2**size):
            for col in range(0, 2**size):
                if DDT[row][col] != 0:
                    subcommand = "(IF {} = 0x{:0>2x} AND {} = 0x{:0>2x} THEN 0x{:0>2x} ELSE {} ENDIF)".format(
                        sin, row, sout, col, size - int(math.log2(DDT[row][col])), subcommand
                    )
    else:
        print("Sbox operation: The sbox size is invalid.")
    return subcommand


def __readDDTForActiveSbox(sin, sout, DDT, size):
    """
    read the look-up table of DDT in CVC format, where active = 1, inactive = 0
    :param sin: the input difference of sbox
    :param sout: the output difference of sbox
    :param DDT: DDT
    :param size: sbox size
    :return: the statement of looking up the differential distribute table
    """
    subcommand = ""
    if size == 4:
        subcommand = "(IF {} = 0x{:0>x} AND {} = 0x{:0>x} THEN 0x0 ELSE 0x{:0>x} ENDIF)".format(sin, 0, sout, 0, size)
        for row in range(1, 2**size):
            for col in range(1, 2**size):
                if DDT[row][col] != 0:
                    subcommand = "(IF {} = 0x{:0>x} AND {} = 0x{:0>x} THEN 0x1 ELSE {} ENDIF)".format(
                        sin, row, sout, col, subcommand
                    )
    elif size == 8:
        subcommand = "(IF {} = 0x{:0>2x} AND {} = 0x{:0>2x} THEN 0x00 ELSE 0x{:0>2x} ENDIF)".format(
            sin, 0, sout, 0, size
        )
        for row in range(0, 2**size):
            for col in range(0, 2*size):
                if DDT[row][col] != 0:
                    subcommand = "(IF {} = 0x{:0>2x} AND {} = 0x{:0>2x} THEN 0x01 ELSE {} ENDIF)".format(
                        sin, row, sout, col, subcommand
                    )
    else:
        print("Sbox operation: The sbox size is invalid.")
    return subcommand


def subCellBasedBlockForDDT(varIN, varOUT, varWGT, sbox, size, mode):
    """
    looking up table based on block
    :param varIN: input differential of sbox -> alpha
    :param varOUT: output differential of sbox -> beta
    :param varWGT: weight of DDT
    :param sbox: sbox
    :param size: the size of sbox
    :param mode: the analysis method. D -> differential; AS -> structure analysis; ID -> impossible differential
    :return: w = if alpha = * and beta = * then * else ...
    """
    command = ""
    ddt = computeDDT(sbox, size)
    if mode == "D":
        tmp_list = np.array(ddt).ravel()[np.flatnonzero(np.array(ddt))].tolist()
        if all(math.log2(num) == 0 for num in tmp_list):
            for i in range(0, len(varIN)):
                command += stp.__equal(varWGT[i], __readDDTForSpecialSbox(varIN[i], varOUT[i], ddt, size))
            for i in range(0, len(varWGT)):
                if size == 4:
                    command += "ASSERT(BVLT({}, 0x4));\n".format(varWGT[i])
                else:
                    command += "ASSERT(BVLT({}, 0x08));\n".format(varWGT[i])
        else:
            for i in range(0, len(varIN)):
                command += stp.__equal(varWGT[i], __readDDT(varIN[i], varOUT[i], ddt, size))
            for i in range(0, len(varWGT)):
                if size == 4:
                    command += "ASSERT(BVGT({}, 0x0));\n".format(varWGT[i])
                else:
                    command += "ASSERT(BVGT({}, 0x00));\n".format(varWGT[i])

    elif mode == "AS" or "ID":
        for i in range(0, len(varIN)):
            command += stp.__equal(varWGT[i], __readDDTForActiveSbox(varIN[i], varOUT[i], ddt, size))
        for i in range(0, len(varWGT)):
            if size == 4:
                command += "ASSERT(BVLT({}, 0x4));\n".format(varWGT[i])
            else:
                command += "ASSERT(BVLT({}, 0x08));\n".format(varWGT[i])

    else:
        print("The analysis mode is not valid!")

    return command


def shuffleCellOperationBasedBlock(var_in, var_out, perm):
    """
    Shuffle cell operation for word-based block ciphers, eg: Midori, CRAFT
    """
    # command = "%%% Permutation %%%\n"
    command = ""
    for i in range(0, len(var_in)):
        command += stp.__equal(var_out[i], var_in[perm[i]])
    return command


def __general_sbox_operation(sin, sbox, size):
    subcommand = ""
    if size == 4:
        subcommand = "0x{:0>x}".format(sbox[0])
        for i in range(1, len(sbox)):
            subcommand = "(IF {} = 0x{:0>x} THEN 0x{:0>x} ELSE {} ENDIF)".format(sin, i, sbox[i], subcommand)
    elif size == 8:
        subcommand = "0x{:0>2x}".format(sbox[0])
        for i in range(1, len(sbox)):
            subcommand = "(IF {} = 0x{:0>2x} THEN 0x{:0>2x} ELSE {} ENDIF)".format(sin, i, sbox[i], subcommand)
    else:
        print("Sbox operation: The sbox size is invalid.")
    return subcommand


def mixcolumnOperationBasedValueForDiff(varIN, varOUT, matrix, order):
    command = ""
    if order == "row":
        tmpIN = ["" for i in range(0, len(varIN))]
        tmpOUT = ["" for j in range(0, len(varOUT))]
        for matRow in range(0, len(matrix)):
            for matCol in range(0, len(matrix[0])):
                tmpIN[matRow * len(matrix) + matCol] = varIN[matCol * len(matrix) + matRow]
                tmpOUT[matRow * len(matrix) + matCol] = varOUT[matCol * len(matrix) + matRow]
        for i in range(0, len(matrix)):
            command += stp.__matrixMultiplyOperation(
                tmpIN[i * len(matrix):(i + 1) * len(matrix)], tmpOUT[i * len(matrix):(i + 1) * len(matrix)], matrix)

    elif order == "col":
        for i in range(0, len(matrix)):
            command += stp.__matrixMultiplyOperation(
                varIN[i * len(matrix):(i + 1) * len(matrix)], varOUT[i * len(matrix):(i + 1) * len(matrix)], matrix)

    else:
        print("mixcolumnOperationBasedValueForDiff: The state order is invalid.")

    return command


def mixcolumnsOperationBasedBlock(varIN, varOUT, matrix, order):
    command = ""
    if order == "row":
        tmpIN = ["" for i in range(0, len(varIN))]
        tmpOUT = ["" for j in range(0, len(varOUT))]
        for matRow in range(0, len(matrix)):
            for matCol in range(0, len(matrix[0])):
                tmpIN[matRow * len(matrix) + matCol] = varIN[matCol * len(matrix) + matRow]
                tmpOUT[matRow * len(matrix) + matCol] = varOUT[matCol * len(matrix) + matRow]
        for i in range(0, len(matrix)):
            command += stp.__matrixMultiplyOperation(
                tmpIN[i * len(matrix):(i + 1) * len(matrix)], tmpOUT[i * len(matrix):(i + 1) * len(matrix)], matrix)

    elif order == "col":
        for i in range(0, len(matrix)):
            command += stp.__matrixMultiplyOperation(
                varIN[i * len(matrix):(i + 1) * len(matrix)], varOUT[i * len(matrix):(i + 1) * len(matrix)], matrix)

    else:
        print("mixcolumnsBasedNibble: The state order is invalid.")

    return command


def subCellBasedNibble(varIN, varOUT, sbox, size):
    command = ""
    for i in range(0, len(varIN)):
        command += stp.__equal(varOUT[i], __general_sbox_operation(varIN[i], sbox, size))
    return command


def getStringXor(var1, var2, var3):
    """
    String values Xor: Z = X ^ Y, where X = (x0, ... xn), Y = (y0, ... yn)
    """
    command = ""
    for i in range(0, len(var1)):
        command += stp.__equal(var3[i], stp.__xor(var1[i], var2[i]))
    return command










