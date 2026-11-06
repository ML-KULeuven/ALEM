import itertools

import numpy as np

import math
import pandas as pd
from matplotlib import pyplot as plt


class Grid:

    def __init__(self, width=10, height=10, initial_cost=1, animals=15, path_grid='', path_threshold='',
                 compute_distances=False):
        if path_grid == '':
            self.width = width
            self.height = height
            self.animals = animals
            self.grid_cost = [[initial_cost for _ in range(self.width)]
                              for _ in range(self.height)]
            self.grid_cost = np.asarray(self.grid_cost)
            self.grid_species = [[[0 for _ in range(self.width)] for _ in range(self.height)] for _ in range(self.animals)]
            self.grid_species = np.asarray(self.grid_species)
            self.species_threshold = [0 for _ in range(self.animals)]
            self.grid_distance = self.compute_matrix_distance() if compute_distances else None
        else:
            df_grid = pd.read_csv(path_grid)
            df_species = pd.read_csv(path_threshold)
            self.height = df_grid['row'].max() + 1
            self.width = df_grid['col'].max() + 1
            species_columns = [column for column in df_grid.columns if column.startswith('specie ')]
            self.animals = len(species_columns)
            self.grid_cost = [[initial_cost for _ in range(self.width)]
                              for _ in range(self.height)]
            self.grid_cost = np.asarray(self.grid_cost)
            self.grid_species = [[[0 for _ in range(self.width)] for _ in range(self.height)] for _ in
                                 range(self.animals)]
            self.species_threshold = [0 for _ in range(self.animals)]
            self.grid_species = np.asarray(self.grid_species)
            self.grid_distance = self.compute_matrix_distance() if compute_distances else None
            for index, row in df_grid.iterrows():
                index_row = int(row['row'])
                index_col = int(row['col'])
                self.grid_cost[index_row][index_col] = row['cost']
                for i, column in enumerate(species_columns):
                    self.grid_species[i][index_row][index_col] = row[column]
            for index, row in df_species.iterrows():
                self.add_specie_threshold(index,row['thr'])

    def compute_matrix_distance(self):
        rows = list(range(self.height))
        cols = list(range(self.width))
        crds = list(itertools.product(rows, cols))
        distance_matrix = np.zeros((self.height, self.width, self.height, self.width), dtype=int)
        for cell_1, cell_2 in itertools.combinations_with_replacement(crds, 2):
            cell_1 = np.asarray(cell_1)
            cell_2 = np.asarray(cell_2)
            distance_matrix[cell_1[0], cell_1[1], cell_2[0], cell_2[1]] = np.abs(cell_1[0] - cell_2[0]) + np.abs(cell_1[1] - cell_2[1])
            distance_matrix[cell_2[0], cell_2[1], cell_1[0], cell_1[1]] = np.abs(cell_1[0] - cell_2[0]) + np.abs(cell_1[1] - cell_2[1])
        return distance_matrix

    def get_distance_matrix(self):
        if self.grid_distance is None:
            self.grid_distance = self.compute_matrix_distance()
        return self.grid_distance


    def add_specie(self, position, cov, size, index_specie):
        distribution = np.random.multivariate_normal(mean=position, cov=[[cov, 0], [0, cov]], size=size)
        for el in distribution:
            if el[0] < self.height and el[1] < self.width:
                self.grid_species[index_specie][math.floor(el[1])][math.floor(el[0])] += 1

    def add_specie_threshold(self, index_specie,threshold):
        self.species_threshold[index_specie] = threshold

    def add_rectangle_constant_cost(self, corner, width, height, cost):
        index_col = min(self.width, corner[1] + width)
        index_row = min(self.height, corner[0] + height)
        for row in range(corner[0], index_row):
            for col in range(corner[1], index_col):
                if self.grid_cost[row][col] < cost:
                    self.grid_cost[row][col] = cost

    def add_circle_constant_cost(self, center, radius, cost):
        index_1_row = max([0, center[0] - radius])
        index_2_row = min([self.height, center[0] + radius + 1])
        index_1_col = max([0, center[1] - radius])
        index_2_col = min([self.width, center[1] + radius + 1])
        for row in range(index_1_row, index_2_row):
            for col in range(index_1_col, index_2_col):
                if np.linalg.norm(np.asarray([row, col]) - np.asarray(center)) <= radius and \
                        self.grid_cost[row][col] < cost:
                    self.grid_cost[row][col] = cost

    def add_circle_gaussian_cost(self, center, radius, cost, std):
        index_1_row = max([0, center[0] - radius])
        index_2_row = min([self.height, center[0] + radius + 1])
        index_1_col = max([0, center[1] - radius])
        index_2_col = min([self.width, center[1] + radius + 1])
        for row in range(index_1_row, index_2_row):
            for col in range(index_1_col, index_2_col):
                multi = np.exp(-((row - center[0]) ** 2 + (col - center[1]) ** 2) / std ** 2)
                cost_cell = multi * cost
                if np.linalg.norm(np.asarray([row, col]) - np.asarray(center)) <= radius and \
                        self.grid_cost[row][col] < cost_cell:
                    self.grid_cost[row][col] = cost_cell

    def convert_into_dfs(self):
        list_dataframe = []
        list_number_specie = []
        for row in range(self.height):
            for col in range(self.width):
                info = []
                info.append(row)
                info.append(col)
                info.append(self.grid_cost[row, col])
                for animal in range(self.animals):
                    info.append(self.grid_species[animal][row][col])
                list_dataframe.append(info)
        for i in range(self.animals):
            list_number_specie.append('specie {}'.format(i))
        columns_df = ['row','col','cost']+list_number_specie
        df_grid = pd.DataFrame(list_dataframe,columns=columns_df)
        df_threshold = pd.DataFrame(self.species_threshold,columns=['thr'])
        return df_grid, df_threshold

    def show_cost_map(self):
        plt.imshow(self.grid_cost, cmap='hot', interpolation='nearest')
        plt.show()

    def show_specie_map(self,index):
        plt.imshow(self.grid_species[index], cmap='hot', interpolation='nearest')
        plt.show()
