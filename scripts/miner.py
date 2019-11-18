#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess
import time
import json
import exploder
import random
import shlex

VERSION = "0.80"  # compress dom + no block + satvar clause and solver nodes

eclat_timeout = 180
eclat_memory_limit = 15*1024*1024
freq_str = "letting min_freq be {}\n"
eclat_size_command = "eclat -tm -s{} -Z {}"
timeout_command = "timeout_perl -t {} -m {} "
conjure_trans_param_command = "conjure translate-param --eprime={} --essence-param={} --eprime-param={} --line-width=2500"
savilerow_command = "savilerow {} {} -run-solver -solutions-to-stdout-one-line -preproc-time-limit 0 -S0"
sat_suffix = " -sat -out-sat {} -sat-family {} -solver-options {}"
minion_suffix = " -minion -out-minion {} -solver-options \"-varorder static\""
info_suffix = " -out-info {}"
cgroups_suffix = " -cgroups"
# -minion-bin minion -preprocess SACBounds_limit"
mkdir_command = "mkdir -p {}"
rm_command = "rm -rf {}"
essence_suffix = ".param"
eprime_suffix = ".eprime-param"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(VERSION))
    parser.add_argument('--mode', action='store',
                        dest='mode', help='Mode (c ar d r)')
    parser.add_argument('--model', action='store',
                        dest='model', help='Eprime model')
    parser.add_argument('--init-param', action='store',
                        dest='init_param', help='Init param')
    parser.add_argument('--freq', action='store',
                        dest='freq', type=int, help='Freq')
    parser.add_argument('--minion', action='store_const', dest='solver_flag',
                        default='nbc', const='minion', help='Use minion')
    parser.add_argument('--glucose', action='store_const', dest='solver_flag',
                        default='nbc', const='glucose', help='Use glucose')
    parser.add_argument('--rnd-seed', action='store', dest='rnd_seed',
                        type=int, default=0, help='Random seed for sat, default 0')
    parser.add_argument('--info', action='store', dest='info_location',
                        default='info-files/', help='Info file location, default info-files')
    parser.add_argument('--tmp', action='store', dest='tmp_location',
                        default='tmp/', help='Info file location, default tmp')
    parser.add_argument('--compress-doms', action='store_true', dest='compress_doms',
                        default=False, help='Compress dominance constraints when incomp is available')
    parser.add_argument('--noblock-dom', action='store_true', dest='noblock_dom',
                        default=False, help='Glucose gets dom nogoods instead of sol block directly')
    parser.add_argument('--cgroups', action='store_true',
                        dest='cgroups_flag', default=False, help='Use Cgroups')
    parser.add_argument('--save-solutions', action='store_true',
                        dest='save_flag', default=False, help='Save solutions to JSON')
    parser.add_argument('--O0', action='store_const',
                        dest='o_flag', default='02', const='O0', help='Use 00')
    parser.add_argument('--O2', action='store_const',
                        dest='o_flag', default='02', const='O2', help='Use O2')
    args = parser.parse_args()
    solve(args.mode, args.model, args.init_param, args.freq, args.solver_flag, args.rnd_seed,
          args.info_location, args.tmp_location, args.cgroups_flag, args.o_flag, args.save_flag, args.compress_doms, args.noblock_dom)


def solve(mode, model, init_param, freq, solver_flag, rnd_seed, info_location, tmp_location, cgroups_flag, o_flag, save_flag, compress_doms, noblock_dom):
    start_time = time.time()
    if "c" != mode and "m" != mode and "ar" != mode and "d" != mode and "r" != mode:
        sys.exit()
    # start_size, eclat_time = get_start_size_from_eclat(freq, init_param)
    # if start_size == 0:
    #     sys.exit(0)
    # elif start_size == -1:
    #     start_size = get_max_row_card(init_param)
    stats = dict()
    # stats["Eclat time"] = eclat_time
    print(mkdir_command.format(tmp_location))
    mkdir_process = subprocess.Popen(mkdir_command.format(
        tmp_location).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(mkdir_process.stdout.readline, b''):
        print(line.decode()[:-1])
    new_essence_param = gen_new_essence_param(
        init_param, essence_suffix, freq, mode)
    init_eprime_param = tmp_location + \
        new_essence_param.split(".")[0].split("/")[-1]+eprime_suffix
    #this is different
    print(mkdir_command.format(info_location))
    mkdir_process = subprocess.Popen(mkdir_command.format(
        info_location).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(mkdir_process.stdout.readline, b''):
        print(line.decode()[:-1])
    print(mkdir_command.format(tmp_location))
    mkdir_process = subprocess.Popen(mkdir_command.format(
        tmp_location).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(mkdir_process.stdout.readline, b''):
        print(line.decode()[:-1])
    low_level_file = model.split(".")[0].split("/")[-1]+"__"+new_essence_param.split(
        ".")[0].split("/")[-1]
    if o_flag == 'O0':
        low_level_file += "_o0"
    else:
        low_level_file += "_o2"
    if compress_doms:
        low_level_file += "_compressed_doms"
    if noblock_dom:
        low_level_file += "_no_block_dom"
    info_file = info_location + low_level_file
    low_level_file = tmp_location + low_level_file
    if "minion" in solver_flag:
        info_file = info_file + "_minion"
    elif "nbc" in solver_flag:
        info_file = info_file + "_nbc"
    elif "glucose" in solver_flag:
        info_file = info_file + "_glucose"
    minion_file = low_level_file+".minion"
    dimacs_file = low_level_file+".dimacs"
    sr_info_file = low_level_file+".info"
    info_file = info_file+"_info.txt"
    new_conjure_command = conjure_trans_param_command.format(
        model, new_essence_param, init_eprime_param)
    print_stdout_and_file(new_conjure_command, info_file, log=True)
    conjure_start_time = time.time()
    conjure_process = subprocess.Popen(
        new_conjure_command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(conjure_process.stdout.readline, b''):
        print_stdout_and_file(line.decode()[:-1], info_file, log=True)
    conjure_end_time = time.time()
    # edit eprime file
    # edit_eprime_file(init_eprime_param, start_size)
    stats["Conjure translate param time"] = conjure_end_time - conjure_start_time
    stats["SolverTotalTime Sum"] = 0
    stats["SavileRowTime Sum"] = 0
    stats["SavileRow Command time"] = 0
    stats["Number of solutions"] = 0
    sr_start_time = time.time()
    # choose targeted solver
    if "glucose" in solver_flag:
        act_sat_suffix = sat_suffix.format(
            dimacs_file, "glucose", "\"-rnd-seed={}\"".format(rnd_seed))
        add_suffix = act_sat_suffix
    elif "nbc" in solver_flag:
        if "noincomp" in model:
            act_sat_suffix = sat_suffix.format(
                dimacs_file, "nbc_minisat_all", "\"-r {} -n {}\"".format(rnd_seed, 1))
        else:
            act_sat_suffix = sat_suffix.format(
                dimacs_file, "nbc_minisat_all", "\"-r {}\"".format(rnd_seed))
        add_suffix = act_sat_suffix
    elif "minion" in solver_flag:
        add_suffix = minion_suffix.format(minion_file)
    new_savilerow_command = savilerow_command.format(
        model, init_eprime_param) + add_suffix + info_suffix.format(sr_info_file)
    if cgroups_flag:
        new_savilerow_command += cgroups_suffix
    if o_flag == 'O0':
        new_savilerow_command += " -O0"
    if compress_doms:
        new_savilerow_command += " -compress-doms"
    if noblock_dom:
        new_savilerow_command += " -noblock-dom"
    print_stdout_and_file(new_savilerow_command, info_file, log=True)
    savilerow_process = subprocess.Popen(shlex.split(
        new_savilerow_command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    solutions = []
    # become leader
    os.setpgrp()
    for line in iter(savilerow_process.stdout.readline, b''):
        code, result, result_occ = get_solution(line.decode(), mode)
        if code == True:
            add_solution(result, result_occ, solutions, mode, save_flag)
        else:
            if line.decode().startswith("Looking"):
                print_stdout_and_file("Solutions so far: {}".format(
                    len(solutions)), info_file, log=True)
            if len(solutions) > 500000:
                print_stdout_and_file(
                    "ERROR : Too many solutions", info_file, log=True)
                os.killpg(0, 15)
                sys.exit(1)
            print_stdout_and_file(line.decode().strip(), info_file, log=True)
    sr_end_time = time.time()
    stats["SavileRow Command time"] += sr_end_time-sr_start_time
    stats = get_savilerow_stats(sr_info_file, stats)
    nc_time_st = time.time()
    # nc_solutions_size = len(exploder.explode_solutions(solutions, init_param))
    stats["Number of solutions"] = len(solutions)
    stats["Number of frequent solutions"] = -1  # nc_solutions_size
    nc_time_end = time.time()
    stats["Exploding frequent solutions time"] = nc_time_end - nc_time_st
    end_time = time.time()
    stats["Script Total time"] = end_time-start_time
    clean_files(new_essence_param, init_eprime_param, minion_file, dimacs_file)
    print_and_store_results(freq, mode, stats, info_file, solutions, save_flag)
    return solutions


def clean_files(new_essence_param, init_eprime_param, minion_file, dimacs_file):
    print(rm_command.format(new_essence_param))
    rm_process = subprocess.Popen(rm_command.format(
        new_essence_param).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(rm_process.stdout.readline, b''):
        print(line.decode()[:-1])
    print(rm_command.format(init_eprime_param))
    rm_process = subprocess.Popen(rm_command.format(
        init_eprime_param).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(rm_process.stdout.readline, b''):
        print(line.decode()[:-1])
    print(rm_command.format(minion_file))
    rm_process = subprocess.Popen(rm_command.format(
        minion_file).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(rm_process.stdout.readline, b''):
        print(line.decode()[:-1])
    print(rm_command.format(dimacs_file))
    rm_process = subprocess.Popen(rm_command.format(
        dimacs_file).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(rm_process.stdout.readline, b''):
        print(line.decode()[:-1])


def edit_eprime_file(init_eprime_param, start_size):
    with open(init_eprime_param, "r") as f:
        lines = f.readlines()

    with open(init_eprime_param, "w") as f:
        f.writelines(lines)
        buff = "letting sizes be [ "
        for i in range(start_size, -1, -1):
            buff += str(i) + ", "
        f.write(buff[:-2]+" ]")


def add_solution(result, result_occ, solutions, mode, save_flag):
    if not save_flag:
        solutions.append(True)
    else:
        sol = {"set_occurrence": result}
        if result_occ is not None:
            sol["count"] = result_occ
        occurrence_sol_to_explicit_sol(sol)
        solutions.append(sol)


def get_solution(line, mode):
    if line.startswith("Solution"):
        if mode == "c":
            solution = line.strip().split(
                "freq_items_1_Occurrence be ")[1].split(';int(')[0] + "]"
            if "freq_items_2" in line:
                solution_occ = line.strip().split(" freq_items_2 be ")[1]
            else:
                solution_occ = None
        elif mode == "m":
            solution = line.strip().split(
                "freq_items_Occurrence be ")[1].split(';int(')[0] + "]"
            solution_occ = None
        elif mode == "ar":
            solution = line.strip().split("lhs_freq_items_1_Occurrence be ")[1].split(';int(')[
                0] + "]" + " -> " + line.strip().split("lhs_freq_items_1_Occurrence be ")[1].split(';int(')[0] + "]"
            solution_occ = line.strip().split("lhs_freq_items_2 be ")[
                1] + " -> " + line.strip().split("rhs_freq_items_2 be ")[1]
        elif mode == "d":
            solution = line.strip().split(
                "freq_items_itemset_Occurrence be ")[1].split(';int(')[0] + "]"
            solution_occ = None
        elif mode == "r":
            solution = line.strip().split(
                "infreq_items_itemset_Occurrence be ")[1].split(';int(')[0] + "]"
            solution_occ = line.strip().split(
                "infreq_items_support be ")[1].split(';int(')[0] + "]"
        return True, solution, solution_occ
    else:
        return False, False, False


def occurrence_sol_to_explicit_sol(solution):
    explicit_sol = []
    split_sol = solution["set_occurrence"][1:-1].split(", ")
    for i in range(len(split_sol)):
        if split_sol[i] == "true":
            explicit_sol.append(i)
    solution["set"] = explicit_sol
    solution.pop("set_occurrence")


def get_savilerow_stats(sr_info_file, stats):
    with open(sr_info_file, "r") as f:
        lines = f.readlines()
    order = -1
    stats["SATVars"] = dict()
    stats["SATClauses"] = dict()
    stats["SolverNodes"] = dict()
    for line in lines:
        if "SolverTotalTime" in line:
            solver_time = line.split(":")[1].split("\n")[0]
            stats["SolverTotalTime Sum"] += float(solver_time)
        elif "SavileRowTotalTime" in line:
            solver_time = line.split(":")[1].split("\n")[0]
            stats["SavileRowTime Sum"] = float(solver_time)
        elif "Partial order" in line:
            order = line.strip().split(": ")[1]
        elif "SATVars" in line:
            a = line.split(":")[1].split("\n")[0]
            stats["SATVars"][order] = a
        elif "SATClauses" in line:
            a = line.split(":")[1].split("\n")[0]
            stats["SATClauses"][order] = a
        elif "SolverNodes" in line:
            a = line.split(":")[1].split("\n")[0]
            stats["SolverNodes"][order] = a
    return stats


def print_and_store_results(freq, mode, stats, info_file, solutions, save_flag):
    info_txt = "Freq: "+str(freq)+"% Mode: "+mode+"\n"
    info_txt += "Script Total Time: "+str(stats["Script Total time"])+"\n"
    # info_txt += "Eclat time: "+str(stats["Eclat time"])+"\n"
    info_txt += "Conjure translate param time: " + \
        str(stats["Conjure translate param time"])+"\n"
    info_txt += "SavileRow Command time: " + \
        str(stats["SavileRow Command time"])+"\n"
    info_txt += "SavileRowTime Sum: "+str(stats["SavileRowTime Sum"])+"\n"
    info_txt += "SolverTotalTime Sum: "+str(stats["SolverTotalTime Sum"])+"\n"
    info_txt += "Exploding frequent solutions time: " + \
        str(stats["Exploding frequent solutions time"])+"\n"
    # info_txt += "Number of frequent solutions: "+str(stats["Number of frequent solutions"])
    info_txt += "SATVars :"+str(stats["SATVars"])+"\n"
    info_txt += "SATClauses :"+str(stats["SATClauses"])+"\n"
    info_txt += "SolverNodes :"+str(stats["SolverNodes"])+"\n"
    info_txt += "Number of solutions: "+str(stats["Number of solutions"])+"\n"
    print_stdout_and_file(info_txt, info_file)
    print("Info stored in "+info_file)
    sols_json = info_file.split(".")[0]+".json"
    if save_flag:
        with open(sols_json, "w") as f:
            json.dump(solutions, f, indent=1)
        print("Solutions stored in "+sols_json)


def gen_new_essence_param(init_param, suffix, freq, mode):
    freq_text = "f_" + str(freq) +  "_" + str(int(random.random()*100000))
    new_param = "{}_{}{}".format(init_param.split(".")[0], freq_text, suffix)
    with open(init_param, "r") as f:
        lines = f.readlines()
    db_starts = []
    db_ends = []
    for i in range(len(lines)):
        line = lines[i]
        if "be mset(" in line or "be sequence(" in line:
            db_starts.append(i+1)
        if ")" in line:
            db_ends.append(i-1)
    freq_count = []
    for i in range(len(db_starts)):
        # this would give diff results in python2-3 and also freq diff
        # nb = math.ceil((db_ends[i] - db_starts[i] + 1)*freq/100)
        nb = round((db_ends[i] - db_starts[i] + 1)*freq/100)
        freq_count.append(nb)
    with open(new_param, "w") as f:
        f.writelines(lines)
        f.write(freq_str.format(freq_count[0]))
        for i in range(1, len(db_starts)):
            f.write(freq_str.replace("freq", "freq_" +
                                    str(i+1)).format(freq_count[i]))
    return new_param


def get_start_size_from_eclat(freq, init_param):
    # hardcode audio temporarily
    if "audio" in init_param:
        return -1, 0
    nb = get_entry_size(init_param)
    occ = round(nb*freq/100)
    index = init_param.rfind("/")
    raw_param = init_param[:index] + \
        init_param[index:].split(".")[0].split("_")[0]+".dat"
    new_eclat_size_command = eclat_size_command.format("-"+str(occ), raw_param)
    new_timeout_command = timeout_command.format(
        eclat_timeout, eclat_memory_limit)
    new_eclat_size_command = new_timeout_command + new_eclat_size_command
    print(new_eclat_size_command)
    eclat_start_time = time.time()
    eclat_process = subprocess.Popen(new_eclat_size_command.split(
    ), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("waiting for eclat to finish")
    size = None
    for line in iter(eclat_process.stdout.readline, b''):
        if "MEM CPU" in line.decode():
            eclat_end_time = time.time()
            eclat_time = eclat_end_time-eclat_start_time
            print("eclat got OOM in {}".format(eclat_time))
            size = -1
        elif "TIMEOUT CPU" in line.decode():
            eclat_end_time = time.time()
            eclat_time = eclat_end_time-eclat_start_time
            print("Eclat got timeout in {}".format(eclat_time))
            size = -1
        elif "FINISHED" in line.decode():
            eclat_end_time = time.time()
            eclat_time = eclat_end_time-eclat_start_time
            print("eclat finished in {}".format(eclat_time))
            break
        else:
            result_line = line
    if "no (frequent) items found" in result_line.decode():
        size = 0
        print("No fis found by eclat in {} s, terminating directly".format(eclat_time))
    if size is None:
        size = int(result_line.decode().split(":")[0].strip())
        print("Maximum cardinality is found as {}".format(size))
    return size, eclat_time


def get_entry_size(init_param):
    index = init_param.rfind("/")
    raw_param = init_param[:index] + \
        init_param[index:].split(".")[0].split("_")[0]+".dat"
    with open(raw_param, "r") as f:
        lines = f.readlines()
        nb = len(lines)
    return nb


def get_max_row_card(param):
    with open(param, "r") as f:
        lines = f.readlines()
    max = 0
    for line in lines:
        count = len(line.split(","))
        if max < count:
            max = count
    return max


def get_item_count(init_param):
    index = init_param.rfind("/")
    raw_param = init_param[:index] + \
        init_param[index:].split(".")[0].split("_")[0]+".dat"
    with open(raw_param, "r") as f:
        lines = f.readlines()
    max_item = -1
    for line in lines:
        for i in line.split():
            if int(i) > max_item:
                max_item = int(i)
    return max_item


def print_help_text():
    print("Usage: python miner.py (m|c) eprime_model essence_init_param freq")
    print("m: maximal fis mining")
    print("c: closed fis mining")
    print("ar: ar mining")


def print_stdout_and_file(given_text, given_file, log=False):
    print(given_text)
    if log:
        given_text = "LOG ENTRY: " + given_text
    with open(given_file, "a") as f:
        f.write(given_text + "\n")


if __name__ == '__main__':
    main()
