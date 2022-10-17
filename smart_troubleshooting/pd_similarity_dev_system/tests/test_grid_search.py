"""
Testing for GridSearch class.

Author: Riccardo Mancini
"""

import numpy as np

from smart_troubleshooting.pd_similarity_dev_system.grid_search \
    import GridSearch


# Make it optimize a 2D parabola
class MockMLP:
    def __init__(self, a, b):
        self._a = a
        self._b = b

    def fit(self, x, y):
        return

    def score(self, x, y):
        return -self._a ** 2 - self._b ** 2


class TestGridSearch:

    def test__make_grid(self):
        grid_search = GridSearch(1)
        combinations = grid_search._make_grid(
            {
                'A': {
                    'min': 0,
                    'max': 10,
                    'step': 5
                },
                'B': {
                    'min': 0,
                    'max': 10,
                    'n': 3
                },
                'C': {
                    'values': ['a', 'b']
                },
            }
        )

        expected_combinations = [
            {'A': 0, 'B': 0, 'C': 'a'},
            {'A': 0, 'B': 0, 'C': 'b'},
            {'A': 0, 'B': 5, 'C': 'a'},
            {'A': 0, 'B': 5, 'C': 'b'},
            {'A': 0, 'B': 10, 'C': 'a'},
            {'A': 0, 'B': 10, 'C': 'b'},
            {'A': 5, 'B': 0, 'C': 'a'},
            {'A': 5, 'B': 0, 'C': 'b'},
            {'A': 5, 'B': 5, 'C': 'a'},
            {'A': 5, 'B': 5, 'C': 'b'},
            {'A': 5, 'B': 10, 'C': 'a'},
            {'A': 5, 'B': 10, 'C': 'b'},
            {'A': 10, 'B': 0, 'C': 'a'},
            {'A': 10, 'B': 0, 'C': 'b'},
            {'A': 10, 'B': 5, 'C': 'a'},
            {'A': 10, 'B': 5, 'C': 'b'},
            {'A': 10, 'B': 10, 'C': 'a'},
            {'A': 10, 'B': 10, 'C': 'b'},
        ]

        for combination in combinations:
            assert combination in expected_combinations
            expected_combinations.remove(combination)

        assert len(expected_combinations) == 0

    def test_search(self):
        grid_search = GridSearch(n_jobs=4, cls=MockMLP)
        score, model = grid_search.search(
            np.empty((100, 10)),
            np.empty((100,)),
            np.empty((10, 10)),
            np.empty((10,)),
            {
                'a': {
                    'min': -10,
                    'max': 10,
                    'step': 0.1
                },
                'b': {
                    'min': -10,
                    'max': 10,
                    'n': 21
                },
            }
        )

        # should all be zeros but some numeric error may be there
        assert abs(score) < 1e-10
        assert abs(model._a) < 1e-10
        assert abs(model._b) < 1e-10
