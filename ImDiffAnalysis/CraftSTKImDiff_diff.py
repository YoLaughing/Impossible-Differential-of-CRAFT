#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
search impossible differential
"""

import os
import copy
import time
import stpcommands as stp
import CraftImDiffModel as model


if __name__ == "__main__":

    parameters = dict()

    parameters["cipher_name"] = "CRAFT"
    parameters["cipher_size"] = 64
    parameters["key_size"] = 128
    parameters["sbox_size"] = 4
    parameters["blocksize"] = 16
    parameters["wordsize"] = 4
    parameters["mode"] = "STKID_diff"

    folder = parameters["cipher_name"] + "_{}_Res".format(parameters["mode"])
    if not os.path.exists(folder):
        os.mkdir(folder)

    search_space = list()
    for i in range(0, parameters["blocksize"]):
        b1 = [0 for ti in range(0, parameters["blocksize"])]
        for val1 in range(1, 16):
            b1[i] = val1
            for j in range(0, parameters["blocksize"]):
                e1 = [0 for ei in range(0, parameters["blocksize"])]
                for val2 in range(1, 16):
                    e1[i] = val2
                    t = [0 for ti in range(0, parameters["blocksize"])]
                    search_space.append(copy.deepcopy([b1, e1, t]))

    parameters["record_file"] = folder + "////" + parameters["cipher_name"] + "_record_{}.txt".format(parameters["mode"])
    parameters["max_record_file"] = folder + "////" + parameters["cipher_name"] + "_record_{}_max.txt".format(parameters["mode"])
    total_search = len(search_space)
    begin_round = 0
    distinguish_rounds = 9
    max_distinguish_rounds = 0
    distinguish_find = True
    while distinguish_find:
        end_round = begin_round + distinguish_rounds
        search_count = 0
        begin_time = time.time()
        distinguish_find = False
        while search_count < len(search_space):
            parameters["key0"] = copy.deepcopy(search_space[search_count][2])
            parameters["key1"] = copy.deepcopy(search_space[search_count][2])
            parameters["tweak"] = copy.deepcopy(search_space[search_count][2])
            parameters["indiff"] = copy.deepcopy(search_space[search_count][0])
            parameters["outdiff"] = copy.deepcopy(search_space[search_count][1])
            parameters["solve_file"] = folder + "////" + parameters["cipher_name"] + "_round{}_{}.stp".format(begin_round, end_round)
            round_inf = [begin_round, end_round]
            t1 = time.time()
            model.modelbuild(parameters, round_inf, parameters["solve_file"])
            flag = stp.solver(parameters["solve_file"])
            os.remove(parameters["solve_file"])
            t2 = time.time()
            print(t2 - t1)
            search_count += 1
            if flag:
                rf = open(parameters["record_file"], "a")
                rf.write("\n{} ".format("*" * 20))
                rf.write("{} round related-tweakey impossible distinguish was found.\n".format(distinguish_rounds))
                rf.write("when the values:\n")
                rf.write("b1 = {}\n".format(stp.listTostring(parameters["indiff"], parameters["sbox_size"])))
                rf.write("e1 = {}\n".format(stp.listTostring(parameters["outdiff"], parameters["sbox_size"])))
                rf.close()
                distinguish_find = True
                break
            else:
                print("testing: round = {}_{}, search_count = {}, total_search = {}".format(
                    begin_round, end_round, search_count, total_search))

        end_time = time.time()
        tf = open(parameters["record_file"], "a")
        if distinguish_find:
            tf.write("After " + str(end_time - begin_time) + "time, we found {} rounds impossible differential.\n\n".format(distinguish_rounds))
            distinguish_rounds += 1
        else:
            tf.write("After " + str(end_time - begin_time) + "time, we show no {} round impossible differential.\n\n".format(distinguish_rounds))
            max_distinguish_rounds = distinguish_rounds - 1
        tf.close()

    search_count = 0
    max_t1 = time.time()
    while search_count < len(search_space):
        parameters["key0"] = copy.deepcopy(search_space[search_count][2])
        parameters["key1"] = copy.deepcopy(search_space[search_count][2])
        parameters["tweak"] = copy.deepcopy(search_space[search_count][2])
        parameters["indiff"] = copy.deepcopy(search_space[search_count][0])
        parameters["outdiff"] = copy.deepcopy(search_space[search_count][1])
        parameters["max_solve_file"] = folder + "////" + parameters["cipher_name"] + "_round{}_{}_max.stp".format(begin_round, begin_round + max_distinguish_rounds)
        round_inf = [begin_round, begin_round + max_distinguish_rounds]

        model.modelbuild(parameters, round_inf, parameters["max_solve_file"])
        flag = stp.solver(parameters["max_solve_file"])

        search_count += 1
        if flag:
            rf = open(parameters["max_record_file"], "a")
            rf.write("\n{} ".format("*" * 20))
            rf.write("{} round related-tweakey impossible distinguish was found.\n".format(distinguish_rounds))
            rf.write("when the values:\n")
            rf.write("b1 = {}\n".format(stp.listTostring(parameters["indiff"], parameters["sbox_size"])))
            rf.write("e1 = {}\n".format(stp.listTostring(parameters["outdiff"], parameters["sbox_size"])))
            rf.close()
        else:
            print("testing: round = {}_{}, search_count = {}, total_search = {}".format(
                begin_round, begin_round + max_distinguish_rounds, search_count, total_search))

    max_t2 = time.time()
    if distinguish_find:
        tf = open(parameters["max_record_file"], "a")
        tf.write("After " + str(max_t2 - max_t1) + "time, we found all {} rounds impossible differential.\n\n".format(
            distinguish_rounds))






