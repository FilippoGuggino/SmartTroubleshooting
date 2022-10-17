"""
This module provides a set of API to access data manipulation functionalities.

Author: Filippo Guggino, Leonardo Cecchelli
"""
import threading
import os
from datetime import datetime
import time

import numpy as np

from smart_troubleshooting.file_io import load_json, dump_json, validate_json
from smart_troubleshooting.pd_similarity_dev_system.similarity_model import SimilarityModel
from smart_troubleshooting.pd_preparation_system.word_embedding_manager import WordEmbeddingManager


class TroubleShootingSystemService:
    """
        This class provides a set of API to access all the functionalities of
        the system. The user interacts with this module by creating a new
        request by the form of a JSON file and replies with a certain
        number of "advised" solutions that the user may choose to implement.
        These are chosen by taking the solutions of the already solved problems
        that the troubleshooting system consider "similar" to the problem sent
        by the user.

        Author: Filippo Guggino
    """
    # pylint: disable=too-many-instance-attributes
    _neural_network_path = "pd_similarity_dev_system/models/output_model.joblib"
    _similar_problem_req_path = "technical_support_system/json/SimilarProblemsReqFile.json"
    _similar_problem_req_schema = \
        "technical_support_system/json/schemas/SimilarProblemsReqSchema.json"
    _candidate_similar_problem_path = "pd_preparation_system/csv/FeatureVectorOutputFile.csv"
    _similar_problem_response_path = "troubleshooting_system/json/SimilarProblemsResponseFile.json"
    _similar_problem_response_schema = \
        "troubleshooting_system/json/schema/SimilarProblemsResponseSchema.json"
    _maxnum_candidate_solution = 10
    _troubleshooting_report_file = "troubleshooting_system/json/troubleshootingReport.json"

    def __init__(self):
        config_path = "troubleshooting_system/json/troubleshootingConfig.json"
        if os.path.exists(config_path):
            self._load_configuration(config_path)

    def _load_configuration(self, config_path):
        config_data = load_json(config_path)
        self._neural_network_path = config_data['neural_network_path']
        self._similar_problem_req_path = config_data['similar_problem_req_path']
        self._similar_problem_req_schema = config_data['similar_problem_req_schema']
        self._candidate_similar_problem_path = config_data['candidate_similar_problem_path']
        self._similar_problem_response_path = config_data['similar_problem_response_path']
        self._similar_problem_response_schema = config_data['similar_problem_response_schema']
        self._maxnum_candidate_solution = config_data['maxnum_candidate_solution']
        self._troubleshooting_report_file = config_data['troubleshooting_report_file']

    def _write_report(self, exit_status, error_message=None):
        report_json = {"exitStatus": exit_status,
                       "errorMessage": error_message,
                       "lastSegregationTime": str(datetime.now())}

        dump_json(report_json, self._troubleshooting_report_file)

    def wait_for_user_problem_data(self):
        """
                Wait for the technical_support_system to create a new SimilarProblemReq.
        """
        if not os.path.exists(self._similar_problem_req_path):
            return False
        return True

    def retrieve_similar_problems_vector(self):
        """
            Retrieve feature vector of previously solved problems from the PD_Preparation_System.

            :return: feature vector and problem id of problems
            :rtype: array of dictionaries of type:
                {<problem_id>, <problem_feature_vector>}
        """
        try:
            with open(self._candidate_similar_problem_path) as problem_mapping_file:
                head_rows = ["problem_id", "problem_feature_vector"]
                csv_rows = np.genfromtxt(
                    problem_mapping_file, delimiter=',',
                    skip_header=1, dtype=str)
                similar_problems_vector = []
                for row in csv_rows:
                    # Convert string representation retrieved from
                    # csv file to Numpy array
                    problem_id = row[0]
                    problem_vector = np.array(row[1:])
                    problem_vector = problem_vector.astype(np.float)
                    problem_embedding = dict(zip(head_rows, [problem_id, problem_vector]))
                    similar_problems_vector.append(problem_embedding)
        except OSError:
            time.sleep(1)
            self.retrieve_similar_problems_vector()
        return similar_problems_vector

    def schedule_troubleshooting_procedure(self, period=1):
        """
            Periodic scheduling of the troubleshooting procedure. Used during
            normal usage of the application, waiting for every request from the user.

            :param period: period (in seconds) between each call of the preparation procedure
            :type period: integer
        """
        self.activate_troubleshooting_procedure()

        threading.Timer(period,  # re-init timer
                        self.schedule_troubleshooting_procedure).start()

    def activate_troubleshooting_procedure(self):
        """
            Retrieve feature vector of previously solved problems from the PD_Preparation_System.

            :return: feature vector and problem id of problems
            :rtype: array of dictionaries of type:
                {<problem_id>, <problem_feature_vector>}
        """
        # self.update_candidate_problems()
        # self.update_neural_model()

        if not os.path.exists(self._neural_network_path):
            return

        neural_network = SimilarityModel.load(self._neural_network_path)
        word_embedding_manager = WordEmbeddingManager()

        # check if a new request has been submitted from the user
        user_request_data = load_json(self._similar_problem_req_path)

        if not user_request_data['requests']:
            return

        user_problem_schema = load_json(
            self._similar_problem_req_schema)
        if validate_json(user_request_data, user_problem_schema) is not True:
            self._write_report(
                "ERROR",
                "There's a problem with the SimilarProblemReqFile, please check schema.")
            print("There's a problem with the SimilarProblemReqFile, please check schema.")
            return

        sentences = [req['problemDescription'] for req in user_request_data['requests']]
        user_problem_vector = word_embedding_manager.create_feature_vector(sentences)
        user_problem_vector = np.array(user_problem_vector[0])

        similar_problems_descriptor = self.retrieve_similar_problems_vector()

        neural_network_input = \
            [problem_des['problem_feature_vector'] - user_problem_vector
             for problem_des in similar_problems_descriptor]

        similarity_results = neural_network.predict(neural_network_input)

        for problem_des, similarity in zip(similar_problems_descriptor, similarity_results):
            # Feature vector is no more used, so it's deleted for two reasons:
            #   - waste of space
            #   - some of these descriptor must be sent back to the user, by removing the
            #       feature vector, dictionary format is adapted to the one requested from the
            #       Technical Support System
            del problem_des['problem_feature_vector']
            problem_des['similarity_percentage'] = similarity

        similar_problems_descriptor = sorted(
            similar_problems_descriptor,
            key=lambda item: item['similarity_percentage'],
            reverse=True)

        candidate_similar_problems = \
            similar_problems_descriptor[:self._maxnum_candidate_solution]

        # Prepare dictionary schema requested from the Technical Support System
        similar_problems_response = {
            "responses": [
                {
                    "requestID": user_request_data['requests'][0]['requestID'],
                    "problemsIDs": []
                }
            ]
        }

        for problem_des in candidate_similar_problems:
            similar_problems_response['responses'][0]["problemsIDs"].append(
                problem_des['problem_id'])

        dump_json(similar_problems_response, self._similar_problem_response_path)
        fresh_req = {"requests": []}
        dump_json(fresh_req, self._similar_problem_req_path)

        self._write_report("OK")
