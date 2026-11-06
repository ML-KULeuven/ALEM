import ast
import itertools
import multiprocessing
import os

import numpy as np
import random
import math
from time import perf_counter
from matplotlib import pyplot as plt
import cpmpy as cpmpy
from cpmpy import *
from cpmpy.solvers import CPM_ortools, CPM_gurobi
from cpmpy.solvers.solver_interface import ExitStatus
from utility.grid_class import Grid




def make_coordinates_pair(solution):
    rows = list(range(solution.shape[0]))
    cols = list(range(solution.shape[1]))
    crds = list(itertools.product(rows, cols))
    coordinates_pair = list(itertools.permutations(crds, 2))
    return coordinates_pair

def compute_matrix_distance(grid):
    rows = list(range(grid.shape[0]))
    cols = list(range(grid.shape[1]))
    coordinates_pair = make_coordinates_pair(grid)
    distance_matrix = np.empty((rows, cols, rows, cols))
    for cell_1, cell_2 in coordinates_pair:
        cell_1 = np.asarray(cell_1)
        cell_2 = np.asarray(cell_2)
        distance_matrix[cell_1[0], cell_1[1], cell_2[0], cell_2[1]] = np.linalg.norm(cell_1 - cell_2)
    return distance_matrix

def compute_matrix_distances(solution):
    rows = list(range(solution.shape[0]))
    cols = list(range(solution.shape[1]))
    coordinates_pair = make_coordinates_pair(solution)
    distance_matrix = np.empty((rows, cols, rows, cols))
    for cell_1, cell_2 in coordinates_pair:
        cell_1 = np.asarray(cell_1)
        cell_2 = np.asarray(cell_2)
        if solution[cell_1==True and cell_2==True]:
            distance_matrix[cell_1[0], cell_1[1], cell_2[0], cell_2[1]] = np.linalg.norm(cell_1 - cell_2)
    return distance_matrix

def make_intervals(tuples,ratio):
    result = []
    tuples.reverse()
    for i in range(len(tuples) - 1):
        obj,lower_bound = tuples[i]
        _,higher_bound = tuples[i+1]
        result.append([lower_bound, higher_bound-1, obj,int((higher_bound-lower_bound)/ratio)])
    return result



def plot(statistics):
    fig, ax = plt.subplots()
    lines = []
    for series in statistics:
        ax.plot(statistics[series][0], statistics[series][1], '-o', color = statistics[series][2],
                linewidth=2, markersize=10, markerfacecolor='red')
        line, = ax.plot(statistics[series][0], statistics[series][1], '-o', color = statistics[series][2],
                         linewidth=2, markersize=10, markerfacecolor='red', label=series)
        lines.append(line)
    ax.set_xlabel('Solutions returned')
    ax.set_ylabel('Time (s)')
    ax.legend(handles=lines, loc='upper left')
    plt.savefig(f'./results/non_dominated_solutions/time_comparison.png')
    plt.show()



def lex_solve(model,objectives,weights,tracker,num_workers):
    fwi_assumption = boolvar(shape=1)
    fit_count = len(objectives) // len(weights)
    rest = len(objectives) % len(weights)
    for i in range(fit_count):
        model.minimize(sum(objectives[i*len(weights):(i+1)*len(weights)]*(weights)))
        if not model.solve(num_workers=num_workers, assumptions=[fwi_assumption],
                           time_limit=tracker.get_remaining_time()):
            return False
        for j in range(len(weights)):
            model += fwi_assumption.implies(objectives[i*len(weights)+j] == objectives[i*len(weights)+j].value())
    if rest > 0:
        model.minimize(sum(np.array(objectives[fit_count*len(weights):fit_count*len(weights)+rest]) * np.array(weights[:rest])))
        if not model.solve(num_workers=num_workers, assumptions=[fwi_assumption], time_limit=tracker.get_remaining_time()):
                return False
    return True


def create_folders(directory):

    folders = directory.split(os.path.sep)
    current_path = ''

    if not folders[0]:
        current_path = os.path.sep  # Set the current path to the root directory
        folders = folders[1:]

    for folder in folders:
        current_path = os.path.join(current_path, folder)
        if not os.path.exists(current_path):
            os.mkdir(current_path)


def solve_lex(model, objectives, time_limit, assumptions):
    constraints = []
    lex_assumptions = assumptions
    for obj in objectives:
        model.minimize(obj)
        if model.solve(num_workers=8, time_limit = time_limit, assumptions=lex_assumptions):
            lex_bool = boolvar()
            constraints.append(obj == obj.value())
            model += lex_bool.implies(cpmpy.all(constraints))
            lex_assumptions = assumptions + [lex_bool]
        else:
            return False
    return True

def solve_lex_batches(model, batches_weights, objectives, time_limit, assumptions):
    counter = 0
    lex_assumptions = assumptions
    constraints = []
    for i in range(len(batches_weights)):
        batch = batches_weights[i]
        obj = np.sum(np.array(batch)*np.array(objectives[counter:(len(batch)+counter)]))
        model.minimize(obj)
        if model.solve(num_workers= multiprocessing.cpu_count(), time_limit = time_limit, log_search_progress = True,
                       assumptions = lex_assumptions):
            input()
            lex_bool = boolvar()
            for obj in objectives[counter:(len(batch)+counter)]:
                constraints.append(obj == obj.value())
            model += lex_bool.implies(cpmpy.all(constraints))
            lex_assumptions = assumptions + [lex_bool]
            counter += len(batch)
        else:
            return False

    return True

def solve_sat_problem(cache,time_limit,new_constraints):
    model_ortools = Model()
    model_ortools = SolverLookup.get('ortools', model_ortools)
    for c in cache:
        model_ortools._post_constraint(c)
    for c in new_constraints:
        model_ortools += c
    if model_ortools.solve(time_limit=time_limit):
        return True
    return False

def exists_solution(cache,to_fix,to_improve):
    fixed_values = [el.args[1] for el in to_fix]
    for sol in cache:
        if fixed_values == sol[:len(fixed_values)]:
            if len(to_improve)==1:
                does_exists = True
                dis = to_improve[0].args
                improved_values = [dis.args[i].args[1] for i in range(len(dis.args))]
                if not any(num1 < num2 for num1, num2 in zip(sol[len(fixed_values):], improved_values)):
                    does_exists = False
                if does_exists:
                    return True
            else:
                does_exists = True
                conjunction_disjunctions = to_improve[0].args
                for dis in conjunction_disjunctions:
                    improved_values = [dis.args[i].args[1] for i in range(len(dis.args))]
                    if not any(num1 < num2 for num1, num2 in zip(sol[len(fixed_values):], improved_values)):
                        does_exists = False
                if does_exists:
                    return True
    return False


def solve_sat_problem(cache,time_limit,new_constraints):
    model_ortools = Model()
    model_ortools = SolverLookup.get('ortools', model_ortools)
    for c in cache:
        model_ortools._post_constraint(c)
    for c in new_constraints:
        model_ortools += c
    if model_ortools.solve(time_limit=time_limit):
        return True
    return False


def general_solve(cache, batches_weights, objectives, time_limit, new_constraints,
                  solver,hint=None):

    if solver=='ortools_assum':
        model = cache
        counter = 0
        list_assumptions = []
        for constraint in new_constraints:
            assumption = boolvar(shape=1)
            model += assumption.implies(constraint)
            list_assumptions.append(assumption)
        for i in range(len(batches_weights)):
            batch = batches_weights[i]
            obj = np.sum(np.array(batch)*np.array(objectives[counter:(len(batch)+counter)]))
            model.minimize(obj)
            if model.solve(assumptions=list_assumptions,num_workers=8, time_limit=time_limit,use_lns=False):
                for obj in objectives[counter:(len(batch)+counter)]:
                    assumption = boolvar(shape=1)
                    model += assumption.implies(obj == obj.value())
                    list_assumptions.append(assumption)
                counter += len(batch)
            else:
                return False
        return True
    if solver=='ortools':
        counter = 0
        constraints = []
        model_ortools = Model()
        model_ortools = SolverLookup.get('ortools', model_ortools)
        # # removes of LNS OLD
        # model_ortools.ort_solver.parameters.use_rins_lns = False
        # model_ortools.ort_solver.parameters.use_feasibility_pump = False
        # model_ortools.ort_solver.parameters.use_lb_relax_lns = False
        model_ortools.ort_solver.parameters.log_search_progress = False
        for c in cache:
            model_ortools._post_constraint(c)
        for cons in new_constraints:
                model_ortools += cons
        for i in range(len(batches_weights)):
            batch = batches_weights[i]
            obj = np.sum(np.array(batch)*np.array(objectives[counter:(len(batch)+counter)]))
            model_ortools.minimize(obj)
            if model_ortools.solve(num_workers=8, time_limit=time_limit,use_lns=False):
                for obj in objectives[counter:(len(batch)+counter)]:
                    constraints.append(obj == obj.value())
                model_ortools += constraints
                counter += len(batch)
            else:
                return False
        return True
    if solver=='gurobi':
        model_gurobi = Model()
        model_gurobi = SolverLookup.get('gurobi', model_gurobi)
        for c in cache:
            model_gurobi._post_constraint(c)
        for cons in new_constraints:
            model_gurobi += cons
        model_gurobi.lex_solve(objectives)
        if model_gurobi.solve(threads=8, time_limit=time_limit):
            return True
        else:
            return False
    if solver=='gurobi_inc':
        model_gurobi = cache
        # CPMpy 0.9's Gurobi interface does not implement solution_hint().
        # Tamby's hint is optional and only affects warm-start performance.
        native = model_gurobi.native_model
        native.update()
        original_constraints = set(native.getConstrs())
        original_variables = set(native.getVars())
        started = perf_counter()
        success = True
        try:
            for cons in new_constraints:
                model_gurobi += cons
            # Current CPMpy no longer provides the repository's old lex_solve,
            # add_temp, and remove_temp extensions. Perform the same strict
            # lexicographic solve explicitly and remove every posted constraint
            # afterwards, keeping the compiled base model persistent.
            for objective in objectives:
                remaining = time_limit - (perf_counter() - started)
                if remaining <= 0:
                    success = False
                    break
                model_gurobi.minimize(objective)
                model_gurobi.solve(threads=8, time_limit=remaining, outputflag=0)
                if model_gurobi.status().exitstatus != ExitStatus.OPTIMAL:
                    success = False
                    break
                model_gurobi += objective == objective.value()
        finally:
            native.update()
            temporary_constraints = [c for c in native.getConstrs() if c not in original_constraints]
            temporary_variables = [v for v in native.getVars() if v not in original_variables]
            if temporary_constraints:
                native.remove(temporary_constraints)
            if temporary_variables:
                native.remove(temporary_variables)
            native.update()
        return success





def compute_obj_value(solution,batch_weights):
    weights = []
    obj_value = 0
    if len(batch_weights)==1:
        weights = batch_weights[0]
    else:
        base_element = batch_weights[0][-2]
        for i in range(len(solution)):
            weights.insert(0,base_element**i)
    for i in range(len(weights)):
        obj_value += solution[i] * weights[i]
    return obj_value


def plot_for_problem(problem,folder,objectives,methods,top_k):
    for filename in os.listdir(folder):
        if any(filename.startswith(str(obj)) for obj in objectives):
            dir_file = os.path.join(folder, filename)
            obj = next((obj for obj in objectives if filename.startswith(str(obj))), None)
            index = objectives.index(obj)
            compute_metrics_problems(folder = dir_file, title=f'{problem} {obj} objectives',
                                     top_k=top_k[index], problems = methods)



def create_batches_weights(default_value,objectives):
    batch_weights = []
    times = math.floor((len(objectives)) / len(default_value))
    for i in range(times):
        batch_weights.append(default_value)
    remaining = ((len(objectives)) % len(default_value))
    if remaining > 0:
        batch_weights.append(default_value[-remaining:])
    return batch_weights

def compute_relative_sparsity(df,objs):
    max_sparsity = int(''.join(['100'] + ['000' for _ in range(objs - 1)]))

    trade_offs = [0 for _ in range(len(ast.literal_eval(df['solution'][0])))]
    solutions = df['solution']
    for i in range(len(solutions) - 2):
        solution = ast.literal_eval(solutions[i])
        next_solution = ast.literal_eval(solutions[i+1])
        index, (elem1, elem2) = next(((i, (x, y)) for i, (x, y)
                                      in enumerate(zip(solution, next_solution)) if x != y), (None, (None, None)))
        trade_offs[index] += 1
        formatted_numbers = [str(num).zfill(3) for num in trade_offs]
        sparsity_str = ''.join(formatted_numbers)
        sparsity = int(sparsity_str) / max_sparsity

    return sparsity


def compute_avg_fixed_values(df,objs,top_k):
    fixed = 0
    solutions = df['solution']
    for i in range(top_k - 1):
        solution = ast.literal_eval(solutions[i])
        next_solution = ast.literal_eval(solutions[i + 1])
        index, (elem1, elem2) = next(((i, (x, y)) for i, (x, y)
                                      in enumerate(zip(solution, next_solution)) if x != y), (None, (None, None)))
        fixed += index
    fixed = (objs - 2) * (top_k - 1) - (fixed)
    return fixed


def dominated(sol1, sol2):
    return all(x <= y for x, y in zip(sol1, sol2)) and any(x < y for x, y in zip(sol1, sol2))

def filter_weakly_dominated(sols,weights):
    filter_dom = [sol2 for i, sol2 in enumerate(sols) if not any(dominated(sol1, sol2) for j, sol1 in enumerate(sols))]
    seen = set()
    filter_weak_dom = [x for x in filter_dom if tuple(x) not in seen and not seen.add(tuple(x))]

    indices_remove = [index for index, element in enumerate(sols) if element not in filter_weak_dom]
    filter_weights = [element for index, element in enumerate(weights) if index not in indices_remove]
    return filter_weak_dom, filter_weights



def distribute_numbers(x, total=15):
    base, remainder = divmod(total, x)
    return [base] * (x - remainder) + [base + 1] * remainder


def remove_sublists(lst_of_lsts, to_remove):
    return [lst for lst in lst_of_lsts if lst not in to_remove]
