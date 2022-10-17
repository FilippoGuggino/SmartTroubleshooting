"""
This module provides a set of API to access data manipulation functionalities.

Author: Filippo Guggino
"""

import string
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from smart_troubleshooting.file_io import load_json, validate_json

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')


class DataManipulationManager:
    """
        This class implements a utility function which perform various data manipulation
        techniques on a vector of sentences:
            - text to lowercase
            - remove punctuation
            - remove stopwords
            - perform stemming: reduce words to their root form
                (e.g. books -> book, looked -> look)
            - perform lemmatization: similar to stemming but uses lexical knoledge to get
                the correct base form (e.g. been -> be, had -> have, etc.)
    """
    # pylint: disable=too-few-public-methods
    _base_configuration_path = \
        "pd_preparation_system/json/basePreparationConfig.json"
    _base_configuration_schema = \
        "pd_preparation_system/json/schemas/basePreparationConfigSchema.json"

    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()
    stop_words = set(stopwords.words('english'))

    def perform_data_manipulation(self, sentences):
        """
            Perform data manipulation on a set of problem descriptions passed
            via parameter "sentences". Data manipulation refers to a set of
            method used on a sentence in order to "normalize" it's content.
            See class docstring for more details.

            :param sentences: problem descriptions to be normalized
            :type sentences: array of strings (problem descriptions)
            :returns: normalized sentences
            :rtype: array of strings
        """

        normalized_sentence_list = []

        base_configuration = load_json(self._base_configuration_path)
        base_configuration_schema = load_json(self._base_configuration_schema)
        if validate_json(base_configuration, base_configuration_schema) is not True:
            print("There's a problem with the BaseConfigurationFile, please check schema. "
                  "Loading Default configuration...")
            base_configuration = {
                "toLowerCase": True,
                "performLemmatization": True,
                "performStemming": True,
                "removeStopwords": True,
                "removePunctuation": True,
                "stopwords": []
            }

        for sentence in sentences:
            if base_configuration['toLowerCase'] is True:
                # To lower case
                sentence = sentence.lower()

            if base_configuration['removePunctuation'] is True:
                # Remove punctuation
                sentence = sentence.translate(str.maketrans("", "", string.punctuation))

            problem_description_words = str(sentence).split(" ")

            if base_configuration['removeStopwords'] is True:
                stop_words = [self.stop_words, base_configuration['stopwords']]
                # Remove stopwords
                problem_description_words = \
                    [i for i in problem_description_words if not i in stop_words]

            normalized_sentence = ""
            for word in problem_description_words:

                if base_configuration['performStemming'] is True:
                    # Perform Stemming
                    word = self.stemmer.stem(word)

                if base_configuration['performLemmatization'] is True:
                    # Perform Lemmatization
                    word = self.lemmatizer.lemmatize(word)

                normalized_sentence += word + " "
            normalized_sentence_list.append(normalized_sentence)
        return normalized_sentence_list
