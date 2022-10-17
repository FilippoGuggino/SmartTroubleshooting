"""
Script for checking validity of pd map and pairs files

This script checks that the problems indicated inside the pairs in the pairs
file (aka {train,validation,test}Set.csv) are a subset of the problems
indicated in the "map" file (aka FeatureVectorOutputFile.csv or
ProblemMappingFile.csv).

Usage: python check_valid_set.py ProblemMappingFile.csv trainSet.csv

Author: Riccardo Mancini
"""

import sys
import numpy as np

if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} ProblemMappingFile.csv trainSet.csv")
    sys.exit(1)

map_file = sys.argv[1]
pairs_file = sys.argv[2]

map_a = np.genfromtxt(map_file, skip_header=1, delimiter=',', dtype=np.str)
pairs_a = np.genfromtxt(pairs_file, skip_header=1, delimiter=',', dtype=np.str)

map_set = set()
for row in map_a:
    map_set.add(row[0])

pairs_set = set()
for row in pairs_a:
    pairs_set.add(row[0])
    pairs_set.add(row[1])

print(sorted(map_set))
print(sorted(pairs_set))

assert map_set >= pairs_set

print("ok")
