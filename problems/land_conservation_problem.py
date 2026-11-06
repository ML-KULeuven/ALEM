import itertools
import timeit

import cpmpy
import numpy as np
from cpmpy import *
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch
import bisect

from utility.utility import distribute_numbers


class LandConModel():

    def __init__(self, grid, obj, compactness_formulation="extrema"):
        if compactness_formulation not in {"extrema", "pairwise"}:
            raise ValueError("compactness_formulation must be 'extrema' or 'pairwise'")
        self.cost = 0
        self.solutions = []
        self.grid = grid
        self.height = grid.grid_cost.shape[0]
        self.width = grid.grid_cost.shape[1]
        for cost_cell in grid.grid_cost:
            self.cost += np.sum(cost_cell)
        self.budget = self.cost // 2
        self.obj = obj
        self.compactness_formulation = compactness_formulation

    def make_model(self):
        variables = {}
        model = Model()

        lands = boolvar(shape=(self.height, self.width), name="lands")
        saved = boolvar(shape=self.grid.animals, name="specie")
        max_compactness = self.grid.height + self.grid.width - 2
        max_population = int(np.sum(self.grid.grid_species))
        compactness = intvar(0, max_compactness, name="compactness")
        sum_saved = intvar(-self.grid.animals, 0, name="sum_saved")
        sum_population = intvar(-max_population, 0, name="sum_population")
        if self.obj > 3:
            new_sum_population = intvar(shape=self.obj - 3, lb=-max_population, ub=0, name="new_sum_population")
        budget_spent = intvar(0, self.budget, name="budget_spent")

        model += (budget_spent == sum(lands * self.grid.grid_cost))
        population = []

        # the lands bought cannot exceed budget
        model += (budget_spent <= (self.budget))
        model += sum_saved == - sum(saved)

        # definition of population
        for animal in range(self.grid.animals):
            population.append(sum(lands * self.grid.grid_species[animal]))
        model += (sum_population == -sum(population))

        # a species is saved if it reaches a threeshold
        for animal in range(self.grid.animals):
            model += (saved[animal] == (population[animal] >= self.grid.species_threshold[animal]))

        rows = range(self.grid.height)
        cols = range(self.grid.width)
        if self.compactness_formulation == "pairwise":
            coordinates = list(itertools.product(rows, cols))
            distance_matrix = self.grid.get_distance_matrix()
            for cell_1, cell_2 in itertools.combinations(coordinates, 2):
                distance = distance_matrix[cell_1[0], cell_1[1], cell_2[0], cell_2[1]]
                model += (-compactness + distance * lands[cell_1] + distance * lands[cell_2]) <= distance
        else:
            # In two dimensions, the maximum Manhattan distance in a selected
            # set is exactly the larger range of (row + col) and (row - col).
            # Tracking those four extrema is equivalent to all pairwise bounds
            # after projecting out the auxiliary variables, but needs O(cells)
            # constraints instead of O(cells**2).
            min_diagonal = -(self.grid.width - 1)
            max_diagonal = self.grid.height - 1
            max_sum = max_compactness
            max_sum_selected = intvar(0, max_sum, name="max_sum_selected")
            min_sum_selected = intvar(0, max_sum, name="min_sum_selected")
            max_diagonal_selected = intvar(min_diagonal, max_diagonal, name="max_diagonal_selected")
            min_diagonal_selected = intvar(min_diagonal, max_diagonal, name="min_diagonal_selected")

            for row, col in itertools.product(rows, cols):
                selected = lands[row, col]
                coordinate_sum = row + col
                coordinate_diagonal = row - col
                model += max_sum_selected >= coordinate_sum - max_compactness * (1 - selected)
                model += min_sum_selected <= coordinate_sum + max_compactness * (1 - selected)
                model += max_diagonal_selected >= coordinate_diagonal - max_compactness * (1 - selected)
                model += min_diagonal_selected <= coordinate_diagonal + max_compactness * (1 - selected)

            model += compactness >= max_sum_selected - min_sum_selected
            model += compactness >= max_diagonal_selected - min_diagonal_selected

        model += (budget_spent == 0).implies(compactness == 0)
        model += (compactness == 0).implies(budget_spent == 0)

        variables['lands'] = lands
        variables['saved'] = saved
        variables['sum_saved'] = sum_saved
        variables['budget_spent'] = budget_spent
        variables['compactness'] = compactness
        variables['solution'] = lands
        variables['population'] = sum_population

        if self.obj == 3:
            default_value = [int(1e5), int(1e2), 1]
            objective_names = ['sum_saved', 'budget_spent', 'compactness']
        if self.obj == 4:
            extinction_risk = distribute_numbers(self.obj - 3, self.grid.animals)
            i = 0
            for index in range(self.obj - 3):
                model += new_sum_population == -sum(
                    [population[animal] for animal in range(i, i + extinction_risk[index])])
                variables[f'population_{index}'] = new_sum_population
                i += extinction_risk[index]
            default_value = [int(1e8), int(1e5), int(1e3), 1]
            objective_names = ['sum_saved', 'budget_spent', 'compactness'] + [f'population_{index}' for index in
                                                                              range(self.obj - 3)]
        if self.obj > 4:
            extinction_risk = distribute_numbers(self.obj - 3, self.grid.animals)
            i = 0
            for index in range(self.obj - 3):
                model += new_sum_population[index] == -sum(
                    [population[animal] for animal in range(i, i + extinction_risk[index])])
                variables[f'population_{index}'] = new_sum_population[index]
                i += extinction_risk[index]
            default_value = [int(1e8), int(1e5), int(1e3), 1]
            objective_names = ['sum_saved', 'budget_spent', 'compactness'] + [f'population_{index}' for index in
                                                                              range(self.obj - 3)]

        return model, variables, objective_names, default_value
