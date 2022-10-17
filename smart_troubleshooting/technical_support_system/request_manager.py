"""
This module provides all the necessary APIs in order to create
new requests or read new responses from the other
applications.

Author: Leonardo Cecchelli
"""

from smart_troubleshooting.file_io import load_json, validate_json, dump_json


class RequestManager:
    """
    This class implements the APIs required to insert a new similar
    problems/solution request and to read
    a new similar problems/solution response. Everything is done
    by using as I/O a set of json files.
    """

    # I/O files
    __new_records_file = \
        "technical_support_system/json/NewRecordsFile.json"
    __solution_request_file = \
        "technical_support_system/json/SolutionRequestsFile.json"
    __solution_response_file = \
        "solved_problems_repo/json/SolutionResponsesFile.json"
    __similar_problems_req_file = \
        "technical_support_system/json/SimilarProblemsReqFile.json"
    __similar_problems_response_file = \
        "troubleshooting_system/json/SimilarProblemsResponseFile.json"

    # json schemas
    __new_records_schema = \
        "solved_problems_repo/json/schemas/NewRecordsFileSchema.json"
    __solution_request_schema = \
        "solved_problems_repo/json/schemas/SolutionRequestsFileSchema.json"
    __solution_response_schema = \
        "solved_problems_repo/json/schemas/SolutionResponsesFileSchema.json"
    __similar_problems_response_schema = \
        "troubleshooting_system/json/schema/SimilarProblemsResponseSchema.json"
    __similar_problems_req_schema = \
        "technical_support_system/json/schemas/SimilarProblemsReqSchema.json"

    def add_similar_problem_req(self, request_id, problem_desc):
        """
        Inserts a new similar problem requests inside the corresponding json file
        :param request_id: the id associated to the request
        :param problem_desc: the problem description
        inserted by the user through the GUI
        """
        req_json = load_json(self.__similar_problems_req_file)
        schema = load_json(self.__similar_problems_req_schema)
        if not validate_json(req_json, schema):
            print("Error: could not validate SimilarProblems.json format")
            return
        prob_req = {
            'requestID': request_id,
            'problemDescription': problem_desc
        }
        req_json["requests"].append(prob_req)
        dump_json(req_json, self.__similar_problems_req_file)

    def add_solution_req(self, request_id, problem_id):
        """
        Inserts a new solution problem requests inside the corresponding json file
        :param request_id: the id associated to the request
        :param problem_id: the id of the problem whose solution wants to be known
        """
        req_json = load_json(self.__solution_request_file)
        schema = load_json(self.__solution_request_schema)
        if not validate_json(req_json, schema):
            print("Error: could not validate SolutionRequests.json format")
            return
        prob_id = str(problem_id)
        sol_req = {
            'requestID': request_id,
            'problemID': prob_id
        }
        req_json["requests"].append(sol_req)
        dump_json(req_json, self.__solution_request_file)

    def add_manual_solution(self, problem_desc, sol_desc, total_presented_sol):
        """
        Inserts a new report about the solution inserted by the user
        into the corresponding json file
        :param problem_desc: the problem description inserted by the
        user through the GUI
        :param sol_desc: the solution description that has been manually
        inserted by the user through the GUI
        :param total_presented_sol: the number of the total displayed solutions
        """
        sol_json = load_json(self.__new_records_file)
        schema = load_json(self.__new_records_schema)
        if not validate_json(sol_json, schema):
            print("Error: could not validate NewRecords.json format")
            return
        new_man_sol = {
            'problemDescription': problem_desc,
            'solutionDescription': sol_desc,
            'isSolutionManual': True,
            'totalPresentedSolutions': total_presented_sol
        }

        sol_json["records"].append(new_man_sol)
        dump_json(sol_json, self.__new_records_file)

    def add_select_solution(self, problem_desc, sol_desc, sol_index, total_presented_sol):
        """
        Inserts a new report about the solution inserted by the user
        into the corresponding json file
        :param problem_desc: the problem description inserted by the
        user through the GUI
        :param sol_desc: the solution description that has been selected
        by the user through the GUI
        :param sol_index: the index of the selected solution
        :param total_presented_sol: the number of the total displayed
        solutions
        """
        sol_json = load_json(self.__new_records_file)
        schema = load_json(self.__new_records_schema)
        if not validate_json(sol_json, schema):
            print("Error: could not validate NewRecords.json format")
            return
        new_sol = {
            'problemDescription': problem_desc,
            'solutionDescription': sol_desc,
            'isSolutionManual': False,
            'solutionIndex': sol_index,
            'totalPresentedSolutions': total_presented_sol
        }
        sol_json["records"].append(new_sol)
        dump_json(sol_json, self.__new_records_file)

    def read_similar_prob(self, request_id):
        """
        Reads all the problems IDs from the response json file
        :param request_id: the id associated to the request
        :return: the requested problems IDs array in case of success,
        an Error message in case of problems
        and a Not Found message if there is no response available at the moment
        """
        data = load_json(self.__similar_problems_response_file)
        schema = load_json(self.__similar_problems_response_schema)
        if not validate_json(data, schema):
            return "Error"
        for prob in data['responses']:
            if prob['requestID'] == request_id:
                return prob['problemsIDs']
        return "Not Found"

    def read_solution(self, request_id):
        """
        Reads the solution description from the response json file
        :param request_id: the id associated to the request
        :return: the requested solution description in case of success,
        an Error message in case of problems
        and a Not Found message if there is no response available at the moment
        """
        data = load_json(self.__solution_response_file)
        schema = load_json(self.__solution_response_schema)
        if not validate_json(data, schema):
            return "Error"
        for prob in data['responses']:
            if prob['requestID'] == request_id and prob['responseType'] == "OK":
                return prob['solutionDescription']
            if prob['requestID'] == request_id and prob['responseType'] != "OK":
                return "Error"
        return "Not Found"

    def flush_solution_responses(self):
        """
        Wipes out all the responses inside the solution response file
        """
        data = {
            "responses": []
        }
        dump_json(data, self.__solution_response_file)
