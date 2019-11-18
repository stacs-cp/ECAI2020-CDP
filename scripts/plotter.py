import json
import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
import matplotlib
import numpy as np
from scipy import stats
import math


def process_solver(new_tree_str, exp, given_key):
    if (given_key in new_tree_str[exp]):
        sol = float(new_tree_str[exp][given_key]["solver_time_mean"])
        sol_err = float(new_tree_str[exp][given_key]["solver_time_mean_error"])
        sr = float(new_tree_str[exp][given_key]["sr_time_v_best"])
        sr_err = float(new_tree_str[exp][given_key]["sr_time_mean_error"])
        nb_sols = new_tree_str[exp][given_key]["sols"]
        nodes = new_tree_str[exp][given_key]["nodes"]
        satc = new_tree_str[exp][given_key]["satc"]
        satv = new_tree_str[exp][given_key]["satv"]
        file_size = new_tree_str[exp][given_key]["file_size"]
        ratio = np.divide(satc, satv)
    else:
        sol = 21600
        sol_err = np.nan
        sr = np.nan
        sr_err = np.nan
        nb_sols = np.nan
        nodes = np.nan
        file_size = np.nan
        ratio = np.nan
    if nb_sols == -1:
        sol = 21600
        sol_err = np.nan
        sr = np.nan
        sr_err = np.nan
        nb_sols = np.nan
        nodes = np.nan
        file_size = np.nan
        ratio = np.nan
    if np.isnan(sol):
        sol = 21600
    return (sol, sol_err, sr, sr_err, nb_sols, nodes, file_size, ratio)



json_file = sys.argv[1]
save=False
if len(sys.argv) > 4:
    if "save" in sys.argv[4]:
        save=True
        

with open(json_file, "r") as jf:
    new_tree_str = json.load(jf)

scatter = []

for exp in new_tree_str:
    if sys.argv[2] in exp:
        min_res = process_solver(new_tree_str, exp, "minion")
        min_n_res = process_solver(new_tree_str, exp, "minion_noincomp")
        nbc_res = process_solver(new_tree_str, exp, "nbc")
        nbc_n_res = process_solver(new_tree_str, exp, "nbc_noincomp")
        glu_res = process_solver(new_tree_str, exp, "glucose")
        glu_n_res = process_solver(new_tree_str, exp, "glucose_noincomp")
        min_n_ord_red = process_solver(new_tree_str, exp, "minion_noincomp_ordered")
        glu_n_ord_red = process_solver(new_tree_str, exp, "glucose_noincomp_ordered")
        min_comp = process_solver(new_tree_str, exp, "minion_compressed")
        nbc_comp = process_solver(new_tree_str, exp, "nbc_compressed")
        sol_sr = (exp, min_res, min_n_res, nbc_res, nbc_n_res, glu_res, glu_n_res, min_n_ord_red, glu_n_ord_red, min_comp, nbc_comp)

        # if (np.isnan(nbc_comp[0]) and not np.isnan(nbc_res[0])):
        #     print(exp)
        # sol = (exp, sat_sol, sat_n_sol, min_sol, min_n_sol, sat_sol_err, sat_n_sol_err, min_sol_err, min_n_sol_err, min_sols, min_n_sols, sat_sols, sat_n_sols)
        # sr = (exp, sat_sr, sat_n_sr, min_sr, min_n_sr, sat_sr_err, sat_n_sr_err, min_sr_err, min_n_sr_err, min_sols, min_n_sols, sat_sols, sat_n_sols)
        
        have_something = False
        for i in range(1, len(sol_sr)):
            # if (not np.isnan(sol_sr[i][0])) and not np.isnan(min_res[0]):
            if (not np.isnan(sol_sr[i][0])):
                if sol_sr[i][0] < 21600:
                    have_something = True
        if have_something:
            scatter.append(sol_sr)
# print(scatter[1])

# scatter_sorted = sorted(scatter_sr, key=lambda x: x[1])

sort_key = 0
if len(sys.argv) > 5:
    if "sort" in sys.argv[5]:
        # nbc
        sort_key = 3
        # minion
        # sort_key = 1

if sort_key == 0:
    scatter_sorted = sorted(scatter, key=lambda x: x[sort_key])
else:
    # solver time
    scatter_sorted = sorted(scatter, key=lambda x: float('inf') if math.isnan(x[sort_key][0]) else x[sort_key][0])
    # nodes
    # scatter_sorted = sorted(scatter, key=lambda x: float('inf') if math.isnan(x[sort_key][5]) else x[sort_key][5])
    # nb
    # scatter_sorted = sorted(scatter, key=lambda x: float('inf') if math.isnan(x[sort_key][4]) else x[sort_key][4])
    # size
    # scatter_sorted = sorted(scatter, key=lambda x: float('inf') if math.isnan(x[sort_key][6]) else x[sort_key][6])

# print(scatter_sorted)
index = 0
for i in scatter_sorted:
    print(str(index) + ' ' + i[0])
    index+=1

# print(scatter_sol_sorted)
fig, ax = plt.subplots(figsize=(10,4))
# fig, ax = plt.subplots(figsize=(12,6))
r1 = np.arange(len(scatter_sorted))
r2 = np.arange(10800)
matplotlib.rc('legend', fontsize=8)


# (sol, sol_err, sr, sr_err, nb_sols)
#  0    1       2       3       4

plot_v = sys.argv[3] 
if "nb" in plot_v:
    p = 4
elif "solver" in plot_v:
    p = 0
elif "total" in plot_v:
    p = 2 
elif "node" in plot_v:
    p = 5
elif "size" in plot_v:
    p = 6
elif 'ratio' in plot_v:
    p = 7

plt.scatter(r1, [row[2][p] for row in scatter_sorted],60, label="Minion CDP_default_order", marker="s", color="green",alpha=0.5, edgecolors ="none")
plt.scatter(r1, [row[7][p] for row in scatter_sorted],60, label="Minion CDP_level_order", marker="s", color="red",alpha=0.5, edgecolors ="none")
plt.scatter(r1, [row[1][p] for row in scatter_sorted],60, label="Minion CDP+I", marker="x", color="blue",alpha=0.5, edgecolors ="none")
plt.scatter(r1, [row[9][p] for row in scatter_sorted],60, label="Minion CDP+I (reformulated)", marker="x", color="orange",alpha=0.5, edgecolors ="none")
plt.scatter(r1, [row[6][p] for row in scatter_sorted],60, label="SAT CDP_default_order", marker="+", color="cyan",alpha=0.5, edgecolors ="none")
plt.scatter(r1, [row[8][p] for row in scatter_sorted],60, label="SAT CDP_level_order", marker="+", color="grey",alpha=0.5, edgecolors ="none")
plt.scatter(r1, [row[3][p] for row in scatter_sorted],60, label="SAT CDP+I", marker="o", color="black",alpha=0.5, edgecolors ="none")
plt.scatter(r1, [row[10][p] for row in scatter_sorted],60, label="SAT CDP+I (reformulated)", marker="o", color="magenta", alpha=0.5, edgecolors ="none")
# plt.scatter(r1, [row[4][0] for row in scatter_sorted],60, label="nbc incomp", marker="s", color="orange")
# plt.scatter(r1, [row[5][0] for row in scatter_sorted],60, label="glucose", marker="s", color="maroon")

# plt.xticks(r1, [x[0] for x in scatter_sorted], rotation='vertical')

# plt.scatter([row[1] for row in scatter_sr_sorted], [row[2] for row in scatter_sr_sorted], 60, marker="x", color="black")
# plt.plot(r2)

if "log" in plot_v:
    plt.yscale('log')

if p == 0:
    # plt.title("solver time")
    plt.ylabel("Time in seconds")
if p == 2:
    plt.title("total time")
    plt.ylabel("time in secs")
elif p == 4:
    plt.title("nb of sols")
elif p == 5:
    plt.title("Total search nodes")
elif p == 6:
    plt.title("End File Size")

plt.xlabel("Instances")

plt.xticks([])

# ax.set_aspect(1.0/ax.get_data_ratio()*0.5)
plt.tight_layout()
# Create legend & Show graphic
plt.legend()
if save:
    if  sort_key == 3 or sort_key == 10:
       plot_v += "_sorted" 
    plt.savefig(sys.argv[2]+"_"+plot_v+".pdf",format="pdf")

else:
    plt.show()
