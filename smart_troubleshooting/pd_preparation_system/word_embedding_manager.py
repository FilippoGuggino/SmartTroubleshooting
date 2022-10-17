"""
    This module provides a set of API in order to generate feature vectors
    from problem descriptions.

    Author: Filippo Guggino
"""
from sentence_transformers import SentenceTransformer
from smart_troubleshooting.pd_preparation_system.data_manipulation_manager \
    import DataManipulationManager


class WordEmbeddingManager:
    """
       This class implements a utility function which translate generate a set of feature vectors
       starting from a vector of sentences. This is used both to train and use the NN.
    """

    model = SentenceTransformer('paraphrase-distilroberta-base-v1')
    data_manipulation_manager = DataManipulationManager()

    def create_feature_vector(self, sentences):
        """
            Generate feature vectors of problem descriptions received through parameter "sentences"

            :param sentences: sentences on which perform data manipulation and sentence embedding.
                ["problem description 1", ... , "problem description n"]
            :type sentences: array of strings (problem descriptions)
            :returns: feature vector of normalized problem description sentences
            :rtype: array of array of float
                [
                    [<feature_vector_1>],
                    ...
                    [<feature_vector_n>]
                ]
        """
        normalized_sentence_list = \
            self.data_manipulation_manager.perform_data_manipulation(sentences)

        sentence_embeddings = self.model.encode(normalized_sentence_list, convert_to_numpy=True)
        sentence_embeddings = [*sentence_embeddings.tolist()]

        return sentence_embeddings
