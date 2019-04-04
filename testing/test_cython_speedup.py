# import pyximport; pyximport.install()
import statistics
import time

import cython_files.generate_neighbor_compiled as generate_neighbor_compiled
import cython_files.makespan_compiled as new_makespan

import solution_factory
from data import Data
from solution import Solution

Data.initialize_data("../data/data_set2/sequenceDependencyMatrix.csv",
                     "../data/data_set2/machineRunSpeed.csv",
                     "../data/data_set2/jobTasks.csv")

# Data.print_data()
op_np_array = solution_factory.get_large_test_operation_np_array()
outer_iters = 10
inner_iters = 1000

print("outer_iterations =", outer_iters)
print("inner iterations =", inner_iters)

make = 0
times = []

for i in range(outer_iters):

    start_time = time.time()
    for j in range(inner_iters):
        make = new_makespan.compute_machine_makespans(op_np_array)

    times.append(time.time() - start_time)

print("compute_machine_makespans()")
print("avg time =", statistics.mean(times), "makespan =", max(make))
print()

times = []
inital_sol = Solution(op_np_array)
sol = None
for i in range(outer_iters):

    start_time = time.time()
    for j in range(inner_iters):
        sol = generate_neighbor_compiled.generate_neighbor(inital_sol, 100)

    times.append(time.time() - start_time)

print("generate_neighbor()")
print("avg time =", statistics.mean(times))
# inital_sol.pprint()
# sol.pprint()
