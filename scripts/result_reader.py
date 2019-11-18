import json
import os
import sys
import numpy as np
from scipy import stats
import re

def main():
    if (len(sys.argv) < 2):
        sys.exit()
    json_file = sys.argv[1]
    results_folder = sys.argv[2]
    read_results_to_json(json_file, results_folder)

def read_results_to_json(json_file, results_folder):
    exps = {}
    count = 0
    for path,dirs,files in os.walk(results_folder):
        for f in files:
            filepath = os.path.join(path, f)
            if "_info.txt" in filepath:
                count +=1
                # relevant_subgroups__vote_30_f_30_45523_o2_nbc_info
                exp_name = filepath.split("_f_")[0].split("/")[-1]
                # print(exp_name)
                # if "noincomp" in filepath:
                #     exp_name += "_noincomp"
                #     exp_name = exp_name + "_" + filepath.split("_")[-2]
                if "minion" in filepath:
                    exp_name += "_minion"
                    # exp_name = exp_name + "_" 
                elif "glucose" in filepath:
                    exp_name += "_glucose"
                    # exp_name = exp_name + "_" 
                else:
                    exp_name += "_nbc"
                    # exp_name = exp_name + "_"
                if "order" in filepath:
                    exp_name += "_ordered"
                if "compress" in filepath:
                    exp_name += "_compressed"
                # print(exp_name)
                while exp_name in exps:
                    exp_name += '0'
                exps[exp_name] = {}
                # a_f = f.replace("_minion","").replace("_info.txt","")
                # rnd = a_f.split("_")[-1]
                # exp_name = exp_name + "_" + rnd
                with open(filepath, "r") as f:
                    lines = f.readlines()
                nb_levels = -1
                prev_lev =  -1
                total_block = 0
                total_block2 = 0
                file_size = -1
                stack_over_flow = False
                for line in lines:
                    if "Number of solutions" in line:
                        exps[exp_name]["sols"] = int(line.strip().split(": ")[1])
                        exps[exp_name]["best_case_nonincomp"] = int(int(exps[exp_name]["sols"]) * (int(exps[exp_name]["sols"]) + 1) / 2)
                        exps[exp_name]["best_case_nonincomp_avg"] = exps[exp_name]["sols"] / 2
                    elif "Number of frequent solutions" in line:
                        exps[exp_name]["freq sols"] = int(line.strip().split(": ")[1])
                    elif "SolverTotalTime" in line:
                        exps[exp_name]["solver_time"] = float(line.strip().split(": ")[1])
                    elif "SavileRow Command time" in line:
                        exps[exp_name]["sr_time"] = float(line.strip().split(": ")[1])
                    elif "SolverNodes" in line:
                        exps[exp_name]["nodes"] = line.strip().replace("\'", "\"").split("SolverNodes :")[1]
                    elif "SATVars" in line:
                        exps[exp_name]["satv"] = line.strip().replace("\'", "\"").split("SATVars :")[1]
                    elif "SATClauses" in line:
                        exps[exp_name]["satc"] = line.strip().replace("\'", "\"").split("SATClauses :")[1]
                    elif "LOG ENTRY:" in line:
                        if "Exception in thread" in line:
                            stack_over_flow = True
                            exps[exp_name]["sols"] = 0
                        if "Looking for solution on incomp value(s): " in line:
                            l_nb_levels = int(line.strip().split(": [")[1][:-1])
                            if l_nb_levels > nb_levels:
                                nb_levels = l_nb_levels
                        if "Solutions so far:" in line:
                            this_lev = int(line.strip().split(": ")[2])
                            if this_lev != prev_lev or prev_lev==-1:
                                total_block2 += this_lev
                            total_block += this_lev
                            prev_lev = this_lev
                        if "Dimacs file size:" in line or "Minion file size: " in line:
                            # print(line)
                            this_file_size = int(line.strip().split("size: ")[1].split(" ")[0])
                            if file_size < this_file_size:
                                file_size = this_file_size
                if stack_over_flow:
                    exps[exp_name]["solver_time"] = np.NaN
                    exps[exp_name]["sr_time"] = np.NaN
                    exps[exp_name]["sols"] = np.NaN
                    exps[exp_name]["memout"] = True
                if nb_levels == -1:
                    nb_levels = np.NaN
                if "solver_time" in exps[exp_name] and exps[exp_name]["solver_time"] > exps[exp_name]["sr_time"]:
                    exps[exp_name]["solver_time"] = np.NaN
                    exps[exp_name]["sr_time"] = np.NaN
                    exps[exp_name]["sols"] = np.NaN
                exps[exp_name]["file_size"] = file_size
                try:
                    if "noincomp" in exp_name:
                        exps[exp_name]["solver_calls"] = int(exps[exp_name]["sols"])+1
                        exps[exp_name]["total_block"] = (int(exps[exp_name]["sols"])+1)*int(exps[exp_name]["sols"])/2
                        exps[exp_name]["avg_block"] = int(exps[exp_name]["sols"])/2  
                        exps[exp_name]["total_block2"] = np.NaN
                    else:    
                        exps[exp_name]["solver_calls"] = nb_levels
                        exps[exp_name]["total_block"] = total_block        
                        exps[exp_name]["total_block2"] = total_block2        
                        exps[exp_name]["avg_block"] = total_block / nb_levels     
                except:
                    exps[exp_name]["solver_calls"] = np.NaN
                    exps[exp_name]["total_block"] = np.NaN
                    exps[exp_name]["total_block2"] = np.NaN
                    exps[exp_name]["avg_block"] = np.NaN      

    tree_str = dict()

    for entry in exps:
        # print(entry)
        # key = entry.split("_")[0] + "_" + entry.split("_")[1][:2]
        # hu_closed_cost_util_freqmining__zoo_10_minion_62956
        # hu_closed_cost_util_freqmining__anneal_10_f_10_6402_o2_compressed_doms_nbc_info
        key =  str(entry.split("_")[:2]) + "_" + str(str(entry.split("__")[1]).split("_")[0:2])
        key = re.sub("(\"|\'|\[|\])", "", key)
        key = key.replace(", ","_")
        if ("minion" in entry):
            sec_key = "minion"
        elif("nbc" in entry):
            sec_key = "nbc"
        elif("glucose" in entry):
            sec_key = "glucose"
        if "noincomp" in entry:
            sec_key += "_noincomp"
        if "order" in entry:
            sec_key += "_ordered"
        if "compress" in entry:
            sec_key += "_compressed"
        if (key not in tree_str):
            tree_str[key] = dict()
        if (sec_key not in tree_str[key]):
            tree_str[key][sec_key] = []
        # print(key)
        # print(sec_key)
        tree_str[key][sec_key].append(exps[entry])



    new_tree_str = dict()
    #median
    for key in tree_str:
        new_tree_str[key] = dict()
        for sec_key in tree_str[key]:
            new_tree_str[key][sec_key] = dict()
            sr_times = []
            solver_times = []
            tot_block = []
            tot2_block = []
            av_block = []
            solver_calls = []
            nb_sols = -1
            nb_sols_array = []
            nodes = []
            satvars = []
            satclauses = []
            file_size_array = []
            for mul in tree_str[key][sec_key]:
                if "sr_time" not in mul or "sols" not in mul:
                    continue
                # fix this to reflect wrong sol count ones to pass
                if nb_sols < mul["sols"]:
                    nb_sols = mul["sols"]
                sr_times.append(float(mul["sr_time"]))
                solver_times.append(float(mul["solver_time"]))
                tot_block.append(float(mul["total_block"]))
                tot2_block.append(float(mul["total_block2"]))
                av_block.append(float(mul["avg_block"]))
                solver_calls.append(mul["solver_calls"])
                nb_sols_array.append(mul["sols"])
                file_size_array.append(mul["file_size"])
                # nodes 
                if "nodes" in mul:
                    try:
                        t_dict = json.loads(mul["nodes"])
                        total_nodes = 0    
                        for i in t_dict:
                            total_nodes += int(t_dict[i])
                        nodes.append(total_nodes)
                    except:
                        a=0
                # satv 
                if "satv" in mul:
                    try:
                        t_dict = json.loads(mul["satv"])
                        t = 0    
                        for i in t_dict:
                            t = int(t_dict[i])
                        satvars.append(t)
                    except:
                        a=0
                # satc 
                if "satc" in mul:
                    try:
                        t_dict = json.loads(mul["satc"])
                        t = 0    
                        for i in t_dict:
                            t = int(t_dict[i])
                        satclauses.append(t)
                    except:
                        a=0
                if "memout" in mul:
                    new_tree_str[key][sec_key]["memout"] = True
                # sr_times.append(np.log(float(mul["sr_time"])))
                # solver_times.append(np.log(float(mul["solver_time"])))
            # if "hypo" in key and "50" in key and "gen" in key and sec_key == "nbc":
            #         print(tot_block)
            new_tree_str[key][sec_key]["solver_time_mean"] = np.nanmean(solver_times)
            new_tree_str[key][sec_key]["sols_array"] = nb_sols_array
            new_tree_str[key][sec_key]["file_size"] = np.nanmean(file_size_array)
            # if "glucose" in sec_key:
            #      print(nb_sols_array)
            try:
                new_tree_str[key][sec_key]["solver_time_v_best"] = np.nanmin(solver_times)
                new_tree_str[key][sec_key]["sr_time_v_best"] = np.nanmin(sr_times)
                new_tree_str[key][sec_key]["total_block_v"] = np.nanmin(tot_block)
            except:
                new_tree_str[key][sec_key]["solver_time_v_best"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_v_best"] = np.NaN
                new_tree_str[key][sec_key]["total_block_v"] = np.NaN
            new_tree_str[key][sec_key]["solver_time_mean_error"] = stats.sem(solver_times)
            if nb_sols == -1:
                nb_sols = np.NaN
            if 'relevant_subgroups_vote_20' in key and 'nbc_compressed' in sec_key:
                print(key, sec_key, solver_times)
            new_tree_str[key][sec_key]["sols"] = nb_sols
            new_tree_str[key][sec_key]["total_block"] = np.nanmean(tot_block)
            new_tree_str[key][sec_key]["total_block2"] = np.nanmean(tot2_block)
            new_tree_str[key][sec_key]["avg_block"] = np.nanmean(av_block)
            new_tree_str[key][sec_key]["solver_calls"] = np.nanmean(solver_calls)
            new_tree_str[key][sec_key]["sr_time_mean"] = np.nanmean(sr_times)
            new_tree_str[key][sec_key]["solver_time_mean_error"] = stats.sem(solver_times)
            new_tree_str[key][sec_key]["sr_time_mean_error"] = stats.sem(sr_times)
            new_tree_str[key][sec_key]['how_many'] = len(list(filter(lambda v: v==v, solver_times)))
            new_tree_str[key][sec_key]['nodes'] = np.nanmean(nodes)
            new_tree_str[key][sec_key]['satv'] = np.nanmean(satvars)
            new_tree_str[key][sec_key]['satc'] = np.nanmean(satclauses)

    #sanitise
    for key in new_tree_str:
        max_sol = -1
        for sec_key in new_tree_str[key]:
            if new_tree_str[key][sec_key]["solver_time_v_best"] > new_tree_str[key][sec_key]["sr_time_v_best"]:
                new_tree_str[key][sec_key]["sols"] = np.NaN
                new_tree_str[key][sec_key]["solver_calls"] = np.NaN
                new_tree_str[key][sec_key]["total_block"] = np.NaN
                new_tree_str[key][sec_key]["total_block2"] = np.NaN
                new_tree_str[key][sec_key]["avg_block"] = np.NaN   
                new_tree_str[key][sec_key]["solver_time_mean"] = np.NaN
                new_tree_str[key][sec_key]["solver_time_v_best"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_mean"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_mean_error"] = np.NaN
                new_tree_str[key][sec_key]["solver_time_mean_error"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_v_best"] = np.NaN
                new_tree_str[key][sec_key]['how_many'] = 0
                new_tree_str[key][sec_key]["sols_array"] = np.NaN
                new_tree_str[key][sec_key]['nodes'] = np.NaN
                new_tree_str[key][sec_key]['satv'] = np.NaN
                new_tree_str[key][sec_key]['satc'] = np.NaN
                new_tree_str[key][sec_key]["file_size"] = np.NaN
            if np.isnan(new_tree_str[key][sec_key]["sols"]):
                new_tree_str[key][sec_key]["sols"] = np.NaN
                new_tree_str[key][sec_key]["solver_calls"] = np.NaN
                new_tree_str[key][sec_key]["total_block"] = np.NaN
                new_tree_str[key][sec_key]["total_block2"] = np.NaN
                new_tree_str[key][sec_key]["avg_block"] = np.NaN   
                new_tree_str[key][sec_key]["solver_time_mean"] = np.NaN
                new_tree_str[key][sec_key]["solver_time_v_best"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_mean"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_mean_error"] = np.NaN
                new_tree_str[key][sec_key]["solver_time_mean_error"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_v_best"] = np.NaN
                new_tree_str[key][sec_key]['how_many'] = 0
                new_tree_str[key][sec_key]["sols_array"] = np.NaN
                new_tree_str[key][sec_key]['nodes'] = np.NaN
                new_tree_str[key][sec_key]['satv'] = np.NaN
                new_tree_str[key][sec_key]['satc'] = np.NaN
                new_tree_str[key][sec_key]["file_size"] = np.NaN
            if "noincomp" not in sec_key:
                if new_tree_str[key][sec_key]["sols"] > max_sol:
                    max_sol = new_tree_str[key][sec_key]["sols"]
        for sec_key in new_tree_str[key]:
            if new_tree_str[key][sec_key]["sols"] == 0 or new_tree_str[key][sec_key]["sr_time_mean"] - new_tree_str[key][sec_key]["solver_time_mean"] > 10000:
                new_tree_str[key][sec_key]["sols"] = np.NaN
                new_tree_str[key][sec_key]["solver_calls"] = np.NaN
                new_tree_str[key][sec_key]["total_block"] = np.NaN
                new_tree_str[key][sec_key]["total_block2"] = np.NaN
                new_tree_str[key][sec_key]["avg_block"] = np.NaN   
                new_tree_str[key][sec_key]["solver_time_mean"] = np.NaN
                new_tree_str[key][sec_key]["solver_time_v_best"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_mean"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_mean_error"] = np.NaN
                new_tree_str[key][sec_key]["solver_time_mean_error"] = np.NaN
                new_tree_str[key][sec_key]["sr_time_v_best"] = np.NaN
                new_tree_str[key][sec_key]['how_many'] = 0
                new_tree_str[key][sec_key]["sols_array"] = np.NaN
                new_tree_str[key][sec_key]['nodes'] = np.NaN
                new_tree_str[key][sec_key]['satv'] = np.NaN
                new_tree_str[key][sec_key]['satc'] = np.NaN
                new_tree_str[key][sec_key]["file_size"] = np.NaN
            if "noincomp" in sec_key:
                if new_tree_str[key][sec_key]["sols"] < max_sol:
                    new_tree_str[key][sec_key]["sols"] = np.NaN
                    new_tree_str[key][sec_key]["solver_calls"] = np.NaN
                    new_tree_str[key][sec_key]["total_block"] = np.NaN
                    new_tree_str[key][sec_key]["total_block2"] = np.NaN
                    new_tree_str[key][sec_key]["avg_block"] = np.NaN   
                    new_tree_str[key][sec_key]["solver_time_mean"] = np.NaN
                    new_tree_str[key][sec_key]["solver_time_v_best"] = np.NaN
                    new_tree_str[key][sec_key]["sr_time_mean"] = np.NaN
                    new_tree_str[key][sec_key]["sr_time_mean_error"] = np.NaN
                    new_tree_str[key][sec_key]["solver_time_mean_error"] = np.NaN
                    new_tree_str[key][sec_key]["sr_time_v_best"] = np.NaN
                    new_tree_str[key][sec_key]['how_many'] = 0
                    new_tree_str[key][sec_key]["sols_array"] = np.NaN
                    new_tree_str[key][sec_key]['nodes'] = np.NaN
                    new_tree_str[key][sec_key]['satv'] = np.NaN
                    new_tree_str[key][sec_key]['satc'] = np.NaN
                    new_tree_str[key][sec_key]["file_size"] = np.NaN

    with open(json_file, "w") as f:
        json.dump(new_tree_str, f, indent=1,  sort_keys=True)
    print("{} experiments processed".format(count))
    
if __name__ == '__main__':
    main()