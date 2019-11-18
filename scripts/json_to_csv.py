import os
import sys
import json
import numpy as np

if (len(sys.argv) < 2):
    sys.exit()
json_file = sys.argv[1]
with open(json_file,"r") as f:
    new_tree_str = json.load(f)

# print("Exp_name, sols, solver_calls, total_blocking, avg_total_blocking, best_case_nonincomp, avg_best_nonincomp, ratio_total, ratio_avg")
# for exp in exps:
#     if ("sols" in exps[exp] and exps[exp]["sols"] > 0):
#         ratio_avg = exps[exp]["avg_block"] / exps[exp]["best_case_nonincomp_avg"]
#         ratio_total = exps[exp]["total_block"] / exps[exp]["best_case_nonincomp"]
#         print(exp, exps[exp]["sols"], exps[exp]["solver_calls"], exps[exp]["total_block"], exps[exp]["avg_block"] ,exps[exp]["best_case_nonincomp"], exps[exp]["best_case_nonincomp_avg"], ratio_total, ratio_avg,sep=',')

print("Exp_name, solver, sols, solver_time_mean, total_time_mean, block,  block(2nd calc) , avg_block, solver_calls, solver_err, sr_err, how_many?, solver_v_best, total_v_best, block_total_v, file_size, nodes, satv, satc")
for exp in new_tree_str:
    for solver in new_tree_str[exp]:
        sols = new_tree_str[exp][solver]["sols"]
        solver_time_mean = new_tree_str[exp][solver]["solver_time_mean"]
        sr_time_mean = new_tree_str[exp][solver]["sr_time_mean"]
        total_block = new_tree_str[exp][solver]["total_block"]
        total_block2 = new_tree_str[exp][solver]["total_block2"]
        avg_block = new_tree_str[exp][solver]["avg_block"]
        solver_calls = new_tree_str[exp][solver]["solver_calls"]
        solver_err = new_tree_str[exp][solver]["solver_time_mean_error"]
        sr_err =new_tree_str[exp][solver]["sr_time_mean_error"]
        how_many =new_tree_str[exp][solver]["how_many"]
        solver_v = new_tree_str[exp][solver]["solver_time_v_best"]
        sr_time_v =new_tree_str[exp][solver]["sr_time_v_best"]
        total_block_v = new_tree_str[exp][solver]["total_block_v"]
        file_size = new_tree_str[exp][solver]["file_size"]
        nodes = new_tree_str[exp][solver]["nodes"]
        satv = new_tree_str[exp][solver]["satv"]
        satc = new_tree_str[exp][solver]["satc"]
        if "noincomp" not in solver:
            n_solver = solver + " D+I"
        else:
            n_solver = solver.replace("_noincomp","") + " D"
        print(exp, n_solver, sols, solver_time_mean, sr_time_mean, total_block, total_block2,avg_block, solver_calls,solver_err,sr_err,how_many, solver_v,sr_time_v ,total_block_v, file_size, nodes, satv, satc, sep=',')