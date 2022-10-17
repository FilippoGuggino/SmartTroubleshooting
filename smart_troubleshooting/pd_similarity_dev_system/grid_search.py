"""
This module provides the implementation of a parallel grid search over the
given parameter ranges.

Author: Riccardo Mancini
"""

from multiprocessing.pool import Pool
from itertools import product
import numpy as np
from progress.bar import Bar

from smart_troubleshooting.pd_similarity_dev_system.similarity_model \
    import SimilarityModel


class GridSearch:
    """This class is an utility for finding the best model parameters
    in the given ranges.

    The search is exhaustive, trying all parameters in the grid in parallel.
    """

    def __init__(self, n_jobs=1, cls=SimilarityModel):
        """Create a new grid search instance

        :param n_jobs: number of parallel workers to use in the grid search
        :type n_jobs: int
        :param cls: the class of the Model to be trained
        """

        self._pool = Pool(n_jobs)
        self._cls = cls

    def _make_grid(self, param_ranges):
        """Return generator of cartesian product of all possible parameter
        values
        """

        param_values = {}

        for param, spec in param_ranges.items():
            if 'min' in spec and 'max' in spec and 'n' in spec:
                if spec['min'] > spec['max']:
                    raise ValueError(f"{param}: min > max")
                if spec['n'] <= 0:
                    raise ValueError(f"{param}: n <= 0")

                if spec.get('scale', 'lin') == 'lin':
                    param_values[param] = np.linspace(
                        spec['min'], spec['max'], spec['n']
                    ).tolist()
                elif spec['scale'] == 'log':
                    param_values[param] = np.logspace(
                        spec['min'], spec['max'], spec['n']
                    ).tolist()
                else:
                    raise ValueError(f"{param}: unrecognized scale "
                                     f"'{spec['scale']}'")
                if spec.get('type', 'float') == 'int':
                    param_values[param] = [int(round(x))
                                           for x in param_values[param]]
            elif 'min' in spec and 'max' in spec and 'step' in spec:
                if spec['min'] > spec['max']:
                    raise ValueError(f"{param}: min > max")

                param_values[param] = []
                tmp = spec['min']
                while tmp <= spec['max']:
                    param_values[param].append(tmp)
                    tmp += spec['step']

            elif 'values' in spec:
                param_values[param] = spec['values']
            else:
                raise ValueError(f"{param}: invalid spec")

        # Cartesian product of all possible parameter values
        return [dict(zip(param_values.keys(), values))
                for values in product(*param_values.values())]

    class Worker:
        """Worker to train and validate multiple models in parallel"""

        def __init__(self, x_train, y_train, x_validate, y_validate, cls):
            """Create a new worker with given parameters.

            Note: since a multiprocessing Pool is used, each process in the
            pool will work on different worker.

            :param x_train: input data to be used for training the models
            :type x_train: ndarray of shape (n_train_samples, n_features)
            :param y_train: expected valued to be used for training the models
            :type y_train: ndarray of shape (n_train_samples,)
            :param x_validate: input data to be used for validating the models
            :type x_validate: ndarray of shape (n_validate_samples, n_features)
            :param y_validate: expected values to be used for validating the
                models
            :type y_validate: ndarray of shape (n_train_samples,)
            :param cls: the class of the Model to be trained
            """
            self.x_train = x_train
            self.y_train = y_train
            self.x_validate = x_validate
            self.y_validate = y_validate
            self._cls = cls

        def __call__(self, params):
            """Train and validate the model

            :param params: model parameters
            :returns: model score and trained model
            """
            model = self._cls(**params)
            model.fit(self.x_train, self.y_train)
            return model.score(self.x_validate, self.y_validate), model

    def search(self, x_train, y_train, x_validate, y_validate, param_ranges):
        """Perfom the parallel grid search over the given parameter ranges.

        The parameter ranges must be specified using the following format:
        {
            'parameter': {
                'min': <minimum value>,
                'max': <maximum value>,
                'step': <step to use>,
                'n': <number of values to try, int>,
                'scale': <one of ['lin','log']>
                'values': <list of possible values, list>,
                'type': <one of ['int', 'float']
            },
            ...
        }

        All parameter attributes are optional but only the following
        combinations are allowed:
         - values: try only the specified values
         - min, max, n, [scale], [type]: try n equally-spaced float values
            between min and max (included). 'scale' can be either 'lin'
            (default) or 'log', in the latter case numbers are spaced evenly
            on a log scale. type is an optional parameter that indicates
            whether to approximate to the closest int or not (default: no).
         - min, max, step: try all values between min and max that have
            a distance k*step from min (k>=0).

        :param x_train: input data to be used for training the models
        :type x_train: ndarray of shape (n_train_samples, n_features)
        :param y_train: expected valued to be used for training the models
        :type y_train: ndarray of shape (n_train_samples,)
        :param x_validate: input data to be used for validating the models
        :type x_validate: ndarray of shape (n_validate_samples, n_features)
        :param y_validate: expected values to be used for validating the models
        :type y_validate: ndarray of shape (n_train_samples,)
        :param param_ranges: the ranges of the parameters in the aforementioned
            format.
        :type param_ranges: dict of dicts
        :return: the trained model with the best accuracy
        :rtype: class:`SimilarityModel`
        """

        worker = GridSearch.Worker(x_train, y_train, x_validate, y_validate,
                                   self._cls)

        grid = self._make_grid(param_ranges)
        bar = Bar('Processing', max=len(grid))

        res = self._pool.imap_unordered(worker, grid)

        best_score = -np.inf
        best_model = None
        for score, model in res:
            if score > best_score:
                best_score = score
                best_model = model
            bar.next()

        bar.finish()

        return best_score, best_model
