"""
Script for injecting a custom dataset as segregation system output

This script takes as input a csv file and overwrites the following files:
segregation_system/csv/{ProblemMappingsFile,trainingSet,validationSet,testSet}.csv

This script can augment the input dataset by repetition. Check the helper
for more information.

Author: Riccardo Mancini
"""

import argparse
import pandas as pd
import numpy as np


def append_swapped(df):
    swapped_df = df.copy().rename(columns={'problem_1_id': 'problem_2_id',
                                           'problem_2_id': 'problem_1_id'})
    return df.append(swapped_df)\
        .reset_index()[['problem_1_id', 'problem_2_id', 'similarity']]


def append_same_problem(df):
    unique1 = df.problem_1_id.unique()
    unique2 = df.problem_2_id.unique()
    unique = np.unique(np.concatenate((unique1, unique2)))
    same_prob_df = pd.DataFrame({
        'problem_1_id': unique,
        'problem_2_id': unique,
        'similarity': [1]*len(unique)
    })
    return df.append(same_prob_df)\
        .reset_index()[['problem_1_id', 'problem_2_id', 'similarity']]


parser = argparse.ArgumentParser(description="Script for injecting a custom "
                                             "dataset as segregation system "
                                             "output")
parser.add_argument('input_file', type=str,
                    help="Path to input csv file"
                    )
parser.add_argument('-r', '--repeat', type=int,
                    help="Number of dataset repetitions",
                    default=1
                    )
parser.add_argument('--training-frac', type=float,
                    help="Fraction of training samples",
                    default=0.7
                    )
parser.add_argument('--validation-frac', type=float,
                    help="Fraction of validation samples",
                    default=0.15
                    )
parser.add_argument('--test-frac', type=float,
                    help="Fraction of test samples",
                    default=0.15
                    )
parser.add_argument('--mapping-file', type=str,
                    help="Path to ProblemMappingsFile to substitute",
                    default="../smart_troubleshooting/segregation_system/csv/"
                            "ProblemMappingFile.csv")
parser.add_argument('--trainingset-file', type=str,
                    help="Path to trainingSet to substitute",
                    default="../smart_troubleshooting/segregation_system/csv/"
                            "trainingSet.csv"
                    )
parser.add_argument('--validationset-file', type=str,
                    help="Path to validationSet to substitute",
                    default="../smart_troubleshooting/segregation_system/csv/"
                            "validationSet.csv"
                    )
parser.add_argument('--testset-file', type=str,
                    help="Path to testSet to substitute",
                    default="../smart_troubleshooting/segregation_system/csv/"
                            "testSet.csv"
                    )


args = parser.parse_args()

input_df = pd.concat(
    [pd.read_csv(args.input_file, index_col=None)]*args.repeat,
    ignore_index=True
)

problem_set = set(input_df[['problem 1', 'problem 2']]
                  .values.flatten().tolist())
problem_df = pd.DataFrame(list(problem_set), columns=["problem"])
problem_df.index.name = 'problem_id'

indexed_df = input_df\
    .merge(problem_df.reset_index(), left_on="problem 1", right_on="problem",
           suffixes=["","1"])\
    .merge(problem_df.reset_index(), left_on="problem 2", right_on="problem",
           suffixes=["","2"])\
    .drop(['problem 1', 'problem 2', 'problem', 'problem2'], axis=1)\
    .rename(columns={'problem_id': 'problem_1_id',
                     'problem_id2': 'problem_2_id',
                     'Similarity': 'similarity'})\
    .reset_index()[['problem_1_id', 'problem_2_id', 'similarity']]

training_df = indexed_df.sample(frac=args.training_frac)
upd_test_frac = args.test_frac/(1-args.training_frac)
test_df = indexed_df.drop(training_df.index).sample(frac=upd_test_frac)
upd_validation_frac = args.validation_frac/(1-args.training_frac-args.test_frac)
validation_df = indexed_df.drop(test_df.index).sample(frac=upd_validation_frac)

problem_df = problem_df.rename(columns={'problem': 'problem description'})
problem_df.index.name = "problem id"

problem_df.to_csv(args.mapping_file)

# double it up to learn symmetry
training_df = append_swapped(training_df)

# add same problem parinings to learn that [0..0] -> 1
training_df = append_same_problem(training_df)
print(training_df)
training_df.to_csv(args.trainingset_file, index=False)

test_df.to_csv(args.testset_file, index=False)

validation_df.to_csv(args.validationset_file, index=False)
