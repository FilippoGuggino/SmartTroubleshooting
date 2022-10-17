"""
This module provides the function that computes the final list of
solutions that are going to be displayed to the user

Author: Leonardo Cecchelli
"""
import time
from smart_troubleshooting.technical_support_system.request_manager import RequestManager
from smart_troubleshooting.file_io import load_json


# global structures
problemsIDs = []
problems_requested = []
solutions = []
request_manager = RequestManager()


def retrieve_solutions():
    """
    Retrieves all the associated solutions to the problems
    IDs gathered from the Troubleshooting system
    :return: an Error message in case of problems or an Ok
    message in case of success
    """
    for prob in problems_requested:
        request_manager.add_solution_req(prob['requestID'], prob['problemID'])
    for prob in problems_requested:
        while True:
            response = request_manager.read_solution(prob['requestID'])
            if response == "Not Found":
                time.sleep(1)
                continue
            if response == "Error":
                return "Error"
            solution = response
            solutions.append(solution)
            break
    print("Retrieving solutions completed")


class SolutionOrganizer:
    """
    This class implements some high level functions that computes the final
    solution list requested by the user through the GUI.
    In particular everything is done by using the APIs provided by
    the request_manager module.
    """

    __config_file = "technical_support_system/json/generalSettings.json"

    def __init__(self):
        """
        Initialize all the session state variables
        """
        self.similar_problem_req_id = 0
        self.presented_sols = 0
        config_json = load_json(self.__config_file)
        if config_json is not None:
            self.num_tries = config_json['number_of_retry']
            if self.num_tries < 10:
                self.num_tries = 200
        else:
            self.num_tries = 200

    def clean_solutions(self):
        """
        Resets all the session state variables in order to prepare
        the module for a new request
        """
        self.similar_problem_req_id = 0
        self.presented_sols = 0
        problemsIDs.clear()
        problems_requested.clear()
        solutions.clear()

    def retrieve_similar_problems(self, problem_description):
        """
        Retrieves all the similar problems IDs in relation to the
        problem description submitted by the user.
        It inserts a new request for the Troubleshooting system
        application and waits for a response.
        :param problem_description: the problem description inserted
        by the user through the GUI
        :return: an Error message in case of problems or an OK
        message in case of success
        """
        self.similar_problem_req_id = self.similar_problem_req_id + 1
        request_manager.add_similar_problem_req(self.similar_problem_req_id, problem_description)

        while True:
            response = request_manager.read_similar_prob(self.similar_problem_req_id)
            if response == "Not Found":
                self.num_tries = self.num_tries + 1
                if self.num_tries == 200:
                    return "Error"
                time.sleep(1)
                continue
            if response == "Error":
                return "Error"
            req_id = 0
            for prob in response:
                req_id = req_id + 1
                entry = {'requestID': req_id, 'problemID': prob}
                problems_requested.append(entry)
            return "Ok"

    def compute_solution_list(self, problem_description):
        """
        Computes the solution list to be sent to the GUI
        :param problem_description: The problem description inserted by the user through the GUI
        :return: the list of solutions or an Error message in case of problems
        """
        res = self.retrieve_similar_problems(problem_description)
        if res == "Error":
            return "No solutions"
        retrieve_solutions()
        if not solutions:
            return "None"
        return solutions
