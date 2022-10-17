"""
This module provides the implementation of the DataLoader class which
simplifies the creation of the datasets from the input files.

Input files are separated into problem list and problem pairings.

Author: Riccardo Mancini
"""

import pandas as pd


class DataLoader:
    """
    This class is used to load the input files into numpy arrays suitable
    for use by the sklearn model.
    """

    def __init__(self, prob_desc_path):
        """Create a new DataLoader instance

        :param prob_desc_path: path to the file containing the embeddings for
            all problem descriptions. This file is expected to be a CSV with
            problem_id as first column and then the embeddings.
        :type prob_desc_path: str
        """

        self._prob_desc = pd.read_csv(prob_desc_path, index_col=0, header=None,
                                      skiprows=1)
        self._prob_desc.index.name = "id"

        self._prob_desc.columns = [
            f"feature{i}"
            for i, _ in enumerate(self._prob_desc.columns)
        ]

    def load(self, pairings_path):
        """Load a pair (input_data, expected_values) from a CSV file of problem
        pairings.

        Problem description embeddings are loaded from ``self._prob_desc``
        and then only the difference of the two problems is kept.

        :param pairings_path: path to a CSV file containing a list of tuples
            (problem1_id, problem2_id, similarity)
        :type pairings_path: str
        :return: the pair of arrays (input_data, expected_values)
        :rtype: tuple(
            ndarray of shape (n_samples, n_features),
            ndarray of shape (n_samples,),
        )
        """

        pairings = pd.read_csv(
            pairings_path,
            names=["problem1_id", "problem2_id", "similarity"],
            skiprows=1
        )

        data_frame = pairings.join(
            self._prob_desc,
            on="problem1_id",
            how="left"
        ).join(
            self._prob_desc,
            on="problem2_id",
            how="left",
            rsuffix='_p2'
        )

        for feature in self._prob_desc.columns:
            data_frame[f"{feature}_diff"] = data_frame[f"{feature}"] - \
                                            data_frame[f"{feature}_p2"]

        input_data = data_frame[
            [f"{ft}_diff" for ft in self._prob_desc.columns]]
        expected_values = data_frame["similarity"]

        return input_data.to_numpy(), expected_values.to_numpy().flatten()

    def get_pd_embeddings(self):
        """Return loaded problem description embedding DataFrame"""

        return self._prob_desc
