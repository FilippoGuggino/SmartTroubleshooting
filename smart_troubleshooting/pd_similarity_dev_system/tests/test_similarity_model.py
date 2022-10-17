"""
Testing for SimilarityModel class.

Author: Riccardo Mancini
"""

import tempfile
import numpy as np
import pytest

from smart_troubleshooting.pd_similarity_dev_system.data_loader \
    import DataLoader
from smart_troubleshooting.pd_similarity_dev_system.similarity_model \
    import SimilarityModel
from smart_troubleshooting.pd_similarity_dev_system.tests.test_utils \
    import path_of


@pytest.mark.parametrize('params', [{'random_state': 0xdeadbeef}])
class TestSimilarityModel:

    def setup_method(self, test_method):
        data_loader = DataLoader(path_of("dummy_problem_embeddings.csv"))
        self.x_train, self.y_train = data_loader.load(
            path_of("dummy_training_set.csv"))
        self.x_validation, self.y_validation = data_loader.load(
            path_of("dummy_validation_set.csv"))
        self.x_test, self.y_test = data_loader.load(
            path_of("dummy_test_set.csv"))

    def test_fit(self, params):
        model = SimilarityModel(**params)
        model.fit(self.x_train, self.y_train)

    def test_get_params(self, params):
        model = SimilarityModel(**params)
        model_params = model.get_params()
        for k, v in params.items():
            assert model_params[k] == v

    def test_predict(self, params):
        model = SimilarityModel(**params)
        model.fit(self.x_train, self.y_train)
        predictions = model.predict(self.x_test)

        assert np.all(predictions >= 0)
        assert np.all(predictions <= 1)
        assert len(predictions) == len(self.y_test)

    def test_score(self, params):
        model = SimilarityModel(**params)
        model.fit(self.x_train, self.y_train)
        score = model.score(self.x_test, self.y_test)

    def test_save(self, params):
        model = SimilarityModel(**params)
        model.fit(self.x_train, self.y_train)
        expected_predictions = model.predict(self.x_test)

        temp_file = tempfile.NamedTemporaryFile()
        model.save(temp_file.name)

        loaded_model = SimilarityModel.load(temp_file.name)
        actual_predictions = loaded_model.predict(self.x_test)

        np.testing.assert_array_equal(expected_predictions, actual_predictions)

        temp_file.close()
