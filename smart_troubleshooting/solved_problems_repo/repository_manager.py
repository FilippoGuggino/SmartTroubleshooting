"""
This module only contains the class RepositoryManager.
It provides the tools to build a MongoDB repository
"""
from datetime import datetime, timedelta
import bson
import pymongo


class RepositoryManager:
    """
    This class implements an API to let other classes interact with the remote MongoDB repository
    """

    def __init__(self):
        """
        Initialize an instance by creating a connection with the remote database
        """
        self.__client = pymongo.MongoClient(
            "mongodb+srv://solvedRepoAdmin:admin@solvedproblemrepocluste."
            "o0pke.mongodb.net/test?retryWrites=true"
            "&w=majority")

        self.__db = self.__client.solvedProblems

    def add_problem(self, problem_description, solution_description):
        """
        Add a solved problem to the database
        :param problem_description: the problem description (in words)
        :param solution_description: the solution description (in words)
        """
        # first of all we ensure that strings are fully lower cases
        problem_description = problem_description.lower()
        solution_description = solution_description.lower()

        solution_json = RepositoryManager.__build_solution(solution_description)

        # first of all we check if the solution is new or already present in the database
        solution = self.__db.solutions.find_one(solution_json)

        if solution is None:  # if it's new, add it to solutions collection
            result = self.__db.solutions.insert_one(solution_json)
            solution_id = result.inserted_id
        else:
            solution_id = solution["_id"]

        problem = RepositoryManager.__build_problem(problem_description, solution_id)
        self.__db.problems.insert_one(problem)
        self.__db.problems.update(problem, {"$currentDate": {"creation_date": True}}, upsert=True)

    def get_solution(self, problem_description):
        """
        Get the solution description of a given solved problem
        :param problem_description: the description of the solved problem
        :return: the description of the solution
        """
        # first of all we ensure that strings are fully lower cases
        problem_description = problem_description.lower()

        problem = self.__db.problems.find_one({"description": problem_description})
        if problem is not None and problem["solution_id"] is not None:
            return self.__db.solutions.find_one({"_id": problem["solution_id"]})["description"]
        return None

    def get_ingestion_records(self, max_age, max_records, keywords):
        """
        Get records ready to be used to ingest Neural Network training
        :param max_age: The maximum age (in days) for a record to be eligible
        :param max_records: The maximum number of records to return
        :param keywords: a list of keywords tha must NOT be present in problem descriptions
        :return: an iterator over the resulting set of documents
        """

        starting_date = datetime.now() - timedelta(days=max_age)

        # build regex: "contains at least one of the keywords"
        regex_str = ""
        is_first = True
        for word in keywords:
            if not is_first:
                regex_str += "|"
            regex_str += word
            is_first = False

        regex = bson.regex.Regex(regex_str)

        filter_json = {
                "creation_date": {"$gte": starting_date},
        }
        # if there are banned keywords add another filter
        if not is_first:
            filter_json["description"] = {"$not": regex}

        result = self.__db.problems.find(filter_json).limit(max_records)

        return result

    def close(self):
        """
        Close an instance of RepositoryManager.
        Should always be called at the end of the usage of each instance.
        """
        self.__client.close()

    @staticmethod
    def __build_problem(description, solution_id):
        return {
            "description": description,
            "solution_id": solution_id
        }

    @staticmethod
    def __build_solution(description):
        return {
            "description": description,
        }
