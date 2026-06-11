[![DOI](https://zenodo.org/badge/914565493.svg)](https://doi.org/10.5281/zenodo.20645358)

# ALEM (Anytime Lexicographic Enumeration for Multi objective problems)

## Overview

ALEM is a Python-based project that implements Multi-objective Anytime Lexicographic Enumeration algorithms. The project aims to solve multi-objective combinatorial optimization problems by proposing two new algorithms: **FI** (Fix, Improved) and **FWI** (Fix, Worsen, Improve), which can efficiently lexicographically enumerate part of the Pareto front.

## Requirements

To install the required dependencies for ALEM, you can use the provided `requirements.txt` file. This file contains all the necessary Python packages to get started.

### Installing Dependencies

1. Clone the repository and navigate to the project directory.

2. Install the requirements using `pip`:

   ```bash
   pip install -r requirements.txt
   ```

3. Additionally, to enable the feature of removing constraints from the Gurobi model, a custom version of `cpmpy` is required. Follow the steps below to install it:

   - Clone the `cpmpy` repository:

     ```bash
     git clone https://github.com/CPMpy/cpmpy.git
     ```

   - Switch to the `transform-then-post` branch:

     ```bash
     git checkout transform-then-post
     ```

   - Install the custom `cpmpy` version in editable mode:

     ```bash
     pip install --editable .
     ```

---

## Running the Experiments

The `runner.py` script is used to run experiments for the ALEM project. You can execute it through the terminal by passing various command-line options to specify the desired enumeration method, problem type, and other configurations.

### Usage

To run the script, use the following command in the terminal:

```bash
python runner.py -m <method> -f <data_folder> -p <problem_type> -k <num_solutions> -s <solver> -t <timeout> -o <objectives>
```

### Explanation of the Options

- **-m**: Specifies the enumeration method to use. You can choose from the following methods (lower case):
  - **fi** : proposed method.
  - **fwi** : proposed method.
  - **disjunction**: Sylva, J., & Crema, A. (2004). *A method for finding the set of non-dominated vectors for multiple objective integer linear programs*. European Journal of Operational Research, 158(1), 46-55. [DOI: 10.1016/S0377-2217(03)00255-8](https://www.sciencedirect.com/science/article/pii/S0377221703002558)
  - **rectangle**: Kirlik, G., & Sayın, S. (2014). *A new algorithm for generating all nondominated solutions of multiobjective discrete optimization problems*. European Journal of Operational Research, 232(3), 479-488. [DOI: 10.1016/j.ejor.2013.08.001](https://www.sciencedirect.com/science/article/pii/S0377221713006474)
  - **ozlen+**: Özlen, M., Burton, B. A., & MacRae, C. A. G. (2014). *Multi-Objective Integer Programming: An Improved Recursive Algorithm*. Journal of Optimization Theory and Applications, 160(2), 470-482. [DOI: 10.1007/s10957-013-0364-y](https://doi.org/10.1007/s10957-013-0364-y)
  - **saugmecon**: Zhang, W., & Reimann, M. (2014). *A simple augmented ε-constraint method for multi-objective mathematical integer programming problems*. European Journal of Operational Research, 234(1), 15-24. [DOI: 10.1016/j.ejor.2013.09.001](https://www.sciencedirect.com/science/article/pii/S0377221713007376)
   - **tamby**: Tamby, S., & Vanderpooten, D. (2021). *Enumeration of the nondominated set of multiobjective discrete optimization problems*. INFORMS Journal on Computing, 33(1), 72-85. [DOI: 10.1287/ijoc.2020.0953](https://doi.org/10.1287/ijoc.2020.0953)
   - **tamby_lex**: Lexicographic variant of tamby
   - **dpa**: Dächert, K., Fleuren, T., & Klamroth, K. (2024). *A simple, efficient and versatile objective space algorithm for multiobjective integer programming*. Mathematical Methods of Operations Research, 100(1), 351–384. [DOI: 10.1007/s00186-023-00841-0](https://doi.org/10.1007/s00186-023-00841-0)

- **-f**: Specifies the folder where the data for each problem type is located. For example, for facility location, you would type:
  ```bash
  -f data/facility/custom
  ```

- **-p**: Specifies the problem type. It can be one of the following:
  - `land`: Land conservation problem
  - `knap`: Knapsack problem
  - `ap`: Assignment problem
  - `facility`: Facility location problem

  Example:
  ```bash
  -p land
  ```

- **-k**: Specifies the number of solutions to return. For example:
  ```bash
  -k 10
  ```

- **-s**: Specifies which solver to use. You can choose between:
  - `gurobi`: Gurobi non incremental
  - `gurobi_inc`: Incremental Gurobi solver (default)

  Example:
  ```bash
  -s gurobi_inc
  ```

- **-t**: Specifies the timeout value in seconds for each experiment. For example:
  ```bash
  -t 300
  ```

- **-o**: Specifies the objectives to consider by passing a series of numbers representing the objective indices. For example:
  ```bash
  -o 3 4 5
  ```

### Example Command

Here is an example of a full command to run an experiment:

```bash
python runner.py -m disjunction -f data/facility/custom -p facility -k 100 -s gurobi_inc -t 300 -o 3 4
```

This command runs the **disjunction** method on a **facility location** problem using the data from `data/facility/custom`, returns 100 solutions, uses the incremental Gurobi solver with a total timeout of 300 seconds and considers 3 and 4 objectives.

---

## Output Folders

When you run the script, it will generate a new folder called `results`, where all the results will be stored. 
Furthermore, all the experimental results of the paper are organized into subfolders corresponding to the research questions and types of results:

- **`plot_Q12`**: This folder contains the results for Research Questions 1 and 2.
- **`plot_Q3`**: This folder contains the results for Research Question 3.
- **`graph`**: This folder contains all the graphs and figures generated for the paper.

---

## Generating Graphs

Graphs and visualizations for the results can be generated by running the code in `plot_results.py`. This script includes examples of how to visualize the results for various research questions and problem types.

