"""
This module provides the implementation of the SimilarityModel class which
is a wrapper around MLPRegressor.

Author: Riccardo Mancini
"""

from sklearn.neural_network import MLPRegressor
from joblib import dump, load


class SimilarityModel:
    """Wrapper class around MLPRegressor"""

    """Which parameters are model hyper params (not training params)"""
    HYPER_PARAMS = ["activation", "hidden_layer_sizes"]

    def __init__(self, model=None, **params):
        """Create new object from given model or create new model from params

        Refer to Sklearn documentation for MLPRegressor for more details about
        the available parameters.

        :param model: a model to back this instance or None if new
            model is to be created, defaults to None
        :type model: class:`MLPRegressor`, optional
        :param params: parameters to pass to ``MLPRegressor(**params)``
        :type params: dict, optional
        :returns: the created instance
        """

        if model is None:
            self._model = MLPRegressor(**params)
        else:
            self._model = model

    def fit(self, input_data, target_values):
        """Fit the model to data matrix input_data and target(s) target_values.

        The input_data is in the form of an array (n_samples, n_features),
        where each sample is the difference between the embeddings of the
        two compared problems.
        The target_values is an array of values between 0 and 1 indicating the
        similarity (1: very similar, 0: not similar at all).

        :param input_data: The input data
        :type input_data: ndarray or sparse matrix of shape
            (n_samples, n_features)
        :param target_values: The target values
        :type target_values: ndarray of shape (n_samples,)
        :returns: self, a trained MLP model
        """

        return self._model.fit(input_data, target_values)

    def get_params(self, deep=False):
        """Get parameters for this estimator.

        Note: this dumps all available parameters on MLPRegressor.

        :param deep: If True, will return the parameters for
            this estimator and contained sub-objects that are estimators,
            defaults to False
        :type deep: bool, optional
        :returns: Parameter names mapped to their values.
        :rtype: dict
        """

        return self._model.get_params(deep)

    def predict(self, input_data):
        """Predict using the multi-layer perceptron model.

        The input_data is in the form of an array (n_samples, n_features),
        where each sample is the difference between the embeddings of the
        two compared problems.
        The result is a flat array where each element is a value between 0 and
        1 indicating the similarity (1: very similar, 0: not similar at all).
        The result is guaranteed to be between 0 and 1 (included).

        :param input_data: The input data
        :type input_data: {array-like, sparse matrix} of shape
            (n_samples, n_features)
        :returns: The predicted values in the range [0,1]
        :rtype: ndarray of shape (n_samples, n_outputs)
        """

        prediction = self._model.predict(input_data)

        # force prediction within the required range
        prediction[prediction < 0] = 0
        prediction[prediction > 1] = 1

        return prediction

    def score(self, test_samples, true_values):
        """Return the coefficient of determination :math:`R^2` of the
        prediction.

        The test_samples is in the form of an array (n_samples, n_features),
        where each sample is the difference between the embeddings of the
        two compared problems.
        The true_values is an array of values between 0 and 1 indicating the
        similarity (1: very similar, 0: not similar at all).

        :param test_samples: Test samples.
        :type test_samples: array-like of shape (n_samples, n_features)
        :param true_values: True values for `test_samples`
        :type true_values: array-like of shape (n_samples,) or
            (n_samples, n_outputs)
        :returns: R^2 of ``self.predict(test_samples)`` wrt. `true_values`.
        :rtype: float
        """
        return self._model.score(test_samples, true_values)

    def save(self, path):
        """Save trained model to file

        This uses joblib to save the file, so it's suggested to use ".joblib"
        as the extension.

        :param path: the path of the file to be created (or replaced)
        """

        dump(self._model, path)

    @staticmethod
    def load(path):
        """Load trained model from file

        The target file must have been generated using the save method.

        :param path: the path to the file to be loaded
        :returns: the loaded model
        :rtype: class:`SimilarityModel`
        """

        model = load(path)
        return SimilarityModel(model=model)
