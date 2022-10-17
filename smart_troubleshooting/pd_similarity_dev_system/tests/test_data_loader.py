"""
Testing for DataLoader class.

Author: Riccardo Mancini
"""

import numpy as np

from smart_troubleshooting.pd_similarity_dev_system.data_loader \
    import DataLoader

from smart_troubleshooting.pd_similarity_dev_system.tests.test_utils \
    import path_of


class TestDataLoader:
    def test_load(self):
        data_loader = DataLoader(path_of("dummy_problem_embeddings.csv"))
        x_train, y_train = data_loader.load(
            path_of("dummy_training_set.csv"))

        expected_x = np.genfromtxt(
            path_of("dummy_training_set_expected_x.csv"),
            delimiter=',')
        expected_y = np.genfromtxt(
            path_of("dummy_training_set_expected_y.csv"),
            delimiter=',')

        np.testing.assert_array_equal(x_train, expected_x)
        np.testing.assert_array_equal(y_train, expected_y)
