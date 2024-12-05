#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import copy
import stpcommands as stp
import differential as diff
import CraftParameters as craft


def add_constants_and_tweakey_operation(var_in, round_constant, tweakey, var_out):
    statement = ""
    for i in range(0, len(var_in)):
        if i == 4:
            statement += "ASSERT({} = BVXOR({}, BVXOR({}, 0bin{})));\n".format(
                var_out[i], var_in[i], tweakey[i], "{:0>8b}".format(round_constant)[0:4]
            )
        elif i == 5:
            statement += "ASSERT({} = BVXOR({}, BVXOR({}, 0bin{})));\n".format(
                var_out[i], var_in[i], tweakey[i], "{:0>8b}".format(round_constant)[4:8]
            )
        else:
            statement += "ASSERT({} = BVXOR({}, {}));\n".format(var_out[i], var_in[i], tweakey[i])
    return statement


def creatSTPforRTKImDiffBasedDiff(parameters, round_inf):
    statement = ""
    decVAR = list()

    x = stp.creatVariablesForSingle("x", round_inf[0], parameters["blocksize"])
    t = stp.creatVariablesForSingle("t", 0, parameters["blocksize"])
    k0 = stp.creatVariablesForSingle("k", 0, parameters["blocksize"])
    k1 = stp.creatVariablesForSingle("k", 1, parameters["blocksize"])

    statement += stp.assertValuesForString(x, parameters["indiff"], parameters["wordsize"])
    statement += stp.assertValuesForString(t, parameters["tweak"], parameters["wordsize"])
    statement += stp.assertValuesForString(k0, parameters["key0"], parameters["wordsize"])
    statement += stp.assertValuesForString(k1, parameters["key1"], parameters["wordsize"])

    decVAR.append(copy.deepcopy(t))
    decVAR.append(copy.deepcopy(k0))
    decVAR.append(copy.deepcopy(k1))

    # key schedule
    tk = list()
    for i in range(0, 4):
        tk.append(stp.creatVariablesForSingle("tk", i, parameters["blocksize"]))
    decVAR += copy.deepcopy(tk)
    statement += stp.getStringXor(k0, t, tk[0])
    statement += stp.getStringXor(k1, t, tk[1])
    statement += stp.getStringXor(k0, stp.getStringPermutation(t, craft.tweakey_permutation), tk[2])
    statement += stp.getStringXor(k1, stp.getStringPermutation(t, craft.tweakey_permutation), tk[3])

    # round function
    for rou in range(round_inf[0], round_inf[1]):
        # round function
        y = stp.creatVariablesForSingle("y", rou, parameters["blocksize"])
        z = stp.creatVariablesForSingle("z", rou, parameters["blocksize"])
        w = stp.creatVariablesForSingle("w", rou, parameters["blocksize"])
        v = stp.creatVariablesForSingle("v", rou, parameters["blocksize"])
        x1 = stp.creatVariablesForSingle("x", rou + 1, parameters["blocksize"])
        decVAR.append(copy.deepcopy(x))
        decVAR.append(copy.deepcopy(y))
        decVAR.append(copy.deepcopy(z))
        decVAR.append(copy.deepcopy(w))
        decVAR.append(copy.deepcopy(v))

        # statement += "%%% Round {}".format(rou+1)
        statement += stp.getStringXor(x, tk[rou % 4], y)
        statement += diff.shuffleCellOperationBasedBlock(y, z, craft.permutation)
        statement += diff.subCellBasedBlockForDDT(z, v, w, craft.sbox, parameters["sbox_size"], parameters["mode"])
        # statement += stp.getVariablesForNonZero(w, parameters["wordsize"])
        statement += diff.mixcolumnOperationBasedValueForDiff(v, x1, craft.matrix, "row")

        x = copy.deepcopy(x1)

    decVAR.append(copy.deepcopy(x))
    y = stp.creatVariablesForSingle("y", round_inf[1], parameters["blocksize"])
    decVAR.append(copy.deepcopy(y))
    statement += diff.getStringXor(x, tk[round_inf[1] % 4], y)
    statement += stp.assertValuesForString(y, parameters["outdiff"], parameters["wordsize"])

    return decVAR, statement


def creatSTPforRTKImDiffBasedValue(parameters, round_inf):
    statement = ""
    decVAR = list()

    x = stp.creatVariablesForMultiple("x", round_inf[0], parameters["blocksize"], parameters["mul"])
    t = stp.creatVariablesForMultiple("t", 0, parameters["blocksize"], parameters["mul"])
    k0 = stp.creatVariablesForMultiple("k", 0, parameters["blocksize"], parameters["mul"])
    k1 = stp.creatVariablesForMultiple("k", 1, parameters["blocksize"], parameters["mul"])

    for i in range(1, parameters["mul"]):
        statement += stp.assertValuesForXorString(x[0], x[i], parameters["indiff"], parameters["wordsize"])
        statement += stp.assertValuesForXorString(t[0], t[i], parameters["tweak"], parameters["wordsize"])
        statement += stp.assertValuesForXorString(k0[0], k0[i], parameters["key0"], parameters["wordsize"])
        statement += stp.assertValuesForXorString(k1[0], k1[i], parameters["key1"], parameters["wordsize"])

    decVAR += copy.deepcopy(t)
    decVAR += copy.deepcopy(k0)
    decVAR += copy.deepcopy(k1)

    # key schedule
    tk = list()
    for i in range(0, 4):
        tk += stp.creatVariablesForMultiple("tk", i, parameters["blocksize"], parameters["mul"])
    decVAR += copy.deepcopy(tk)
    for i in range(0, parameters["mul"]):
        statement += diff.getStringXor(k0[i], t[i], tk[i])
        statement += diff.getStringXor(k1[i], t[i], tk[parameters["mul"] + i])
        statement += diff.getStringXor(
            k0[i], stp.getStringPermutation(t[i], craft.tweakey_permutation), tk[parameters["mul"] * 2 + i]
        )
        statement += diff.getStringXor(
            k1[i], stp.getStringPermutation(t[i], craft.tweakey_permutation), tk[parameters["mul"] * 3 + i]
        )

    # round function
    for rou in range(round_inf[0], round_inf[1]):
        y = stp.creatVariablesForMultiple("y", rou, parameters["blocksize"], parameters["mul"])
        z = stp.creatVariablesForMultiple("z", rou, parameters["blocksize"], parameters["mul"])
        x1 = stp.creatVariablesForMultiple("x", rou+1, parameters["blocksize"], parameters["mul"])
        decVAR += copy.deepcopy(x)
        decVAR += copy.deepcopy(y)
        decVAR += copy.deepcopy(z)

        for m in range(0, parameters["mul"]):
            statement += add_constants_and_tweakey_operation(x[m], craft.round_constants[rou], tk[(rou % 4) * 2 + m], y[m])
            tmp = stp.getStringPermutation(y[m], craft.permutation)
            statement += diff.subCellBasedNibble(tmp, z[m], craft.sbox, parameters["sbox_size"])
            statement += diff.mixcolumnsOperationBasedBlock(z[m], x1[m], craft.matrix, "row")

        x = copy.deepcopy(x1)

    y = stp.creatVariablesForMultiple("y", round_inf[1], parameters["blocksize"], parameters["mul"])
    decVAR += copy.deepcopy(x)
    decVAR += copy.deepcopy(y)
    for m in range(0, parameters["mul"]):
        statement += add_constants_and_tweakey_operation(
            x[m], craft.round_constants[round_inf[1]], tk[(round_inf[1] % 4) * 2 + m], y[m]
        )

    for i in range(1, parameters["mul"]):
        statement += stp.assertValuesForXorString(y[0], y[i], parameters["outdiff"], parameters["wordsize"])

    return decVAR, statement


def creatSTPforSTKImDiffBasedDiff(parameters, round_inf):
    statement = ""
    decVAR = list()

    x = stp.creatVariablesForSingle("x", round_inf[0], parameters["blocksize"])
    t = stp.creatVariablesForSingle("t", 0, parameters["blocksize"])
    k0 = stp.creatVariablesForSingle("k", 0, parameters["blocksize"])
    k1 = stp.creatVariablesForSingle("k", 1, parameters["blocksize"])

    statement += stp.assertValuesForString(x, parameters["indiff"], parameters["wordsize"])
    statement += stp.assertValuesForString(t, parameters["tweak"], parameters["wordsize"])
    statement += stp.assertValuesForString(k0, parameters["key0"], parameters["wordsize"])
    statement += stp.assertValuesForString(k1, parameters["key1"], parameters["wordsize"])

    decVAR.append(copy.deepcopy(t))
    decVAR.append(copy.deepcopy(k0))
    decVAR.append(copy.deepcopy(k1))

    # key schedule
    tk = list()
    for i in range(0, 4):
        tk.append(stp.creatVariablesForSingle("tk", i, parameters["blocksize"]))
    decVAR += copy.deepcopy(tk)
    statement += diff.getStringXor(k0, t, tk[0])
    statement += diff.getStringXor(k1, t, tk[1])
    statement += diff.getStringXor(k0, stp.getStringPermutation(t, craft.tweakey_permutation), tk[2])
    statement += diff.getStringXor(k1, stp.getStringPermutation(t, craft.tweakey_permutation), tk[3])

    # round function
    for rou in range(round_inf[0], round_inf[1]):
        # round function
        y = stp.creatVariablesForSingle("y", rou, parameters["blocksize"])
        z = stp.creatVariablesForSingle("z", rou, parameters["blocksize"])
        w = stp.creatVariablesForSingle("w", rou, parameters["blocksize"])
        v = stp.creatVariablesForSingle("v", rou, parameters["blocksize"])
        x1 = stp.creatVariablesForSingle("x", rou + 1, parameters["blocksize"])
        decVAR.append(copy.deepcopy(x))
        decVAR.append(copy.deepcopy(y))
        decVAR.append(copy.deepcopy(z))
        decVAR.append(copy.deepcopy(w))
        decVAR.append(copy.deepcopy(v))

        statement += diff.subCellBasedBlockForDDT(x, y, w, craft.sbox, parameters["sbox_size"], "ID")
        statement += diff.mixcolumnOperationBasedValueForDiff(y, z, craft.matrix, "row")
        statement += diff.getStringXor(z, tk[rou % 4], v)
        statement += diff.shuffleCellOperationBasedBlock(v, x1, craft.permutation)

        x = copy.deepcopy(x1)

    decVAR.append(copy.deepcopy(x))
    y = stp.creatVariablesForSingle("y", round_inf[1], parameters["blocksize"])
    w = stp.creatVariablesForSingle("w", round_inf[1], parameters["blocksize"])
    decVAR.append(copy.deepcopy(y))
    decVAR.append(copy.deepcopy(w))
    statement += diff.subCellBasedBlockForDDT(x, y, w, craft.sbox, parameters["sbox_size"], "ID")
    statement += stp.assertValuesForString(y, parameters["outdiff"], parameters["wordsize"])

    return decVAR, statement


def creatSTPforSTKImDiffBasedValue(parameters, round_inf):
    statement = ""
    decVAR = list()

    x = stp.creatVariablesForMultiple("x", round_inf[0], parameters["blocksize"], parameters["mul"])
    t = stp.creatVariablesForMultiple("t", 0, parameters["blocksize"], parameters["mul"])
    k0 = stp.creatVariablesForMultiple("k", 0, parameters["blocksize"], parameters["mul"])
    k1 = stp.creatVariablesForMultiple("k", 1, parameters["blocksize"], parameters["mul"])

    for i in range(1, parameters["mul"]):
        statement += stp.assertValuesForXorString(x[0], x[i], parameters["indiff"], parameters["wordsize"])
        statement += stp.assertValuesForXorString(t[0], t[i], parameters["tweak"], parameters["wordsize"])
        statement += stp.assertValuesForXorString(k0[0], k0[i], parameters["key0"], parameters["wordsize"])
        statement += stp.assertValuesForXorString(k1[0], k1[i], parameters["key1"], parameters["wordsize"])

    decVAR += copy.deepcopy(t)
    decVAR += copy.deepcopy(k0)
    decVAR += copy.deepcopy(k1)

    # key schedule
    tk = list()
    for i in range(0, 4):
        tk += stp.creatVariablesForMultiple("tk", i, parameters["blocksize"], parameters["mul"])
    decVAR += copy.deepcopy(tk)
    for i in range(0, parameters["mul"]):
        statement += diff.getStringXor(k0[i], t[i], tk[i])
        statement += diff.getStringXor(k1[i], t[i], tk[parameters["mul"] + i])
        statement += diff.getStringXor(
            k0[i], stp.getStringPermutation(t[i], craft.tweakey_permutation), tk[parameters["mul"] * 2 + i]
        )
        statement += diff.getStringXor(
            k1[i], stp.getStringPermutation(t[i], craft.tweakey_permutation), tk[parameters["mul"] * 3 + i]
        )

    # round function
    for rou in range(round_inf[0], round_inf[1]):
        y = stp.creatVariablesForMultiple("y", rou, parameters["blocksize"], parameters["mul"])
        z = stp.creatVariablesForMultiple("z", rou, parameters["blocksize"], parameters["mul"])
        w = stp.creatVariablesForMultiple("w", rou, parameters["blocksize"], parameters["mul"])
        x1 = stp.creatVariablesForMultiple("x", rou+1, parameters["blocksize"], parameters["mul"])
        decVAR += copy.deepcopy(x)
        decVAR += copy.deepcopy(y)
        decVAR += copy.deepcopy(z)

        for m in range(0, parameters["mul"]):
            statement += diff.subCellBasedNibble(x[m], y[m], craft.sbox, parameters["sbox_size"])
            statement += diff.mixcolumnsOperationBasedBlock(y[m], z[m], craft.matrix, "row")
            statement += add_constants_and_tweakey_operation(z[m], craft.round_constants[rou], tk[(rou % 4) * 2 + m], w[m])
            statement += diff.shuffleCellOperationBasedBlock(w[m], x1[m], craft.permutation)
        x = copy.deepcopy(x1)

    y = stp.creatVariablesForMultiple("y", round_inf[1], parameters["blocksize"], parameters["mul"])
    decVAR += copy.deepcopy(x)
    decVAR += copy.deepcopy(y)
    for m in range(0, parameters["mul"]):
        statement += diff.subCellBasedNibble(x[m], y[m], craft.sbox, parameters["sbox_size"])

    for i in range(1, parameters["mul"]):
        statement += stp.assertValuesForXorString(y[0], y[i], parameters["outdiff"], parameters["wordsize"])

    return decVAR, statement


def modelbuild(parameters, round_inf, stpFILE):
    statement = ""
    statement += "%%% The model for single tweakey impossible differential\n"
    statement += "%%% For {}: n = {}, r = {};\n".format(parameters["cipher_name"], parameters["cipher_size"], round_inf)

    if parameters["mode"] == "STKID_diff":
        all_var, statement1 = creatSTPforSTKImDiffBasedDiff(parameters, round_inf)
        statement += stp.getStringForVariables(all_var, parameters["wordsize"])
        statement += statement1
        statement += stp.setupQuery()

    elif parameters["mode"] == "STKID_value":
        all_var, statement1 = creatSTPforSTKImDiffBasedValue(parameters, round_inf)
        statement += stp.getStringForVariables(all_var, parameters["wordsize"])
        statement += statement1
        statement += stp.setupQuery()

    elif parameters["mode"] == "RTKID_diff":
        all_var, statement1 = creatSTPforRTKImDiffBasedDiff(parameters, round_inf)
        statement += stp.getStringForVariables(all_var, parameters["wordsize"])
        statement += statement1
        statement += stp.setupQuery()

    elif parameters["mode"] == "RTKID_value":
        all_var, statement1 = creatSTPforRTKImDiffBasedValue(parameters, round_inf)
        statement += stp.getStringForVariables(all_var, parameters["wordsize"])
        statement += statement1
        statement += stp.setupQuery()

    else:
        print("ImDiffAnalysis for CRAFT: The analysis is not valid!")

    if os.path.exists(stpFILE):
        os.remove(stpFILE)
    f = open(stpFILE, "a")
    f.write(statement)
    f.close()




