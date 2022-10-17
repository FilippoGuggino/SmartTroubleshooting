"""
This module offers an API to make testing easier and replicable
Author: L. Bacciottini, F. Guggino
"""
import datetime
import os
import time
import numpy as np

from smart_troubleshooting.file_io import \
    load_json, validate_json, dump_json, read_csv, dump_csv_array
from smart_troubleshooting.pd_similarity_dev_system.tests.test_main import \
    MockArgs
from smart_troubleshooting.segregation_system.pd_segregation_system import \
    PDSegregationSystem
from smart_troubleshooting.solved_problems_repo.repository_manager import \
    RepositoryManager
from smart_troubleshooting.solved_problems_repo.repository_service import \
    RepositoryService
from smart_troubleshooting.pd_preparation_system.pd_preparation_system_service \
    import PDPreparationSystemService
from smart_troubleshooting.troubleshooting_system.troubleshooting_system_service import \
    TroubleShootingSystemService
from smart_troubleshooting.pd_similarity_dev_system.main import _main


class TestingFactory:
    """
    This class offers an API to run tests and measure the system performances
    """
    @staticmethod
    def test_training_pipeline(max_records):
        """
        Run the whole machine learning pipeline from ingestion to training phase.
        :param max_records: the maximum number of ingestion records for this test (workload)
        :return: The total time of execution of this test.
        None if an error occurred.
        """

        starting_time = datetime.datetime.now().timestamp()

        # step 1: ingestion
        print("performing ingestion step...")
        repository = RepositoryService()
        repo_config_filename = "./solved_problems_repo/json/IngestionConfig.json"
        repo_config_filename_schema = "./solved_problems_repo/json/" \
            "schemas/IngestionConfigSchema.json"
        repo_config_json = load_json(repo_config_filename)
        repo_config_schema = load_json(repo_config_filename_schema)
        if not validate_json(repo_config_json, repo_config_schema):
            print("Testing error: repository configuration is not compliant with its schema")
            return None
        repo_config_json["maxNumberOfRecords"] = max_records
        dump_json(repo_config_json, repo_config_filename)
        repository.activate_ingestion_procedure()

        ingestion_report_filename = "./solved_problems_repo/json/IngestionReport.json"
        ingestion_report = load_json(ingestion_report_filename)
        if ingestion_report["exitStatus"] != "OK":
            print("Testing error: ingestion step failed: " + ingestion_report["errorMessage"])
            return None

        # step 2: segregation
        print("performing segregation step...")
        segregation_system = PDSegregationSystem()
        segregation_system.activate_segregation_procedure()
        segregation_report_filename = "./segregation_system/json/segregationReport.json"
        segregation_report = load_json(segregation_report_filename)
        if segregation_report["exitStatus"] != "OK":
            print("Testing error: segregation step failed: " + segregation_report["errorMessage"])
            return None

        # step 3: preparation
        print("performing preparation step...")
        pd_preparation_service = PDPreparationSystemService()
        pd_preparation_service.activate_pd_preparation_procedure()

        # step 4: training
        print("performing training, test and validation step...")
        args = MockArgs("manual_train",
                        "./pd_similarity_dev_system/json/examples/manual_train_config.json")
        _main(args)

        # evaluate elapsed time and return it
        ending_time = datetime.datetime.now().timestamp()
        return ending_time - starting_time

    @staticmethod
    def test_problem_submission_pipeline(problems_count):
        """
        Simulate the submission of "problems_count" problems to the system
        and their processing. Human steps are automatized and their execution
        time is set to a constant value.
        :param problems_count: The number of problems to be submitted to the system
        :return: The total time of execution of this test.
        None if an error occurred.
        """

        # load problems to submit from dummy set
        problems = load_json("./testing/json/dummy_problems.json")

        starting_time = datetime.datetime.now().timestamp()

        similar_problem_req_path = "technical_support_system/json/SimilarProblemsReqFile.json"
        similar_problem_response_path = \
            "troubleshooting_system/json/SimilarProblemsResponseFile.json"
        repository_update_path = "technical_support_system/json/NewRecordsFile.json"

        troubleshooting_manager = TroubleShootingSystemService()
        troubleshooting_manager.schedule_troubleshooting_procedure()

        print(problems)
        for index, problem in enumerate(problems):
            if index >= problems_count:
                break
            print(problem)
            # Simulate user that requests a set of possible solutions
            # from the Troubleshooting System
            TestingFactory.generate_problem_req_file(similar_problem_req_path, index, problem)
            # Wait for solutions from troubleshooting system
            TestingFactory.wait_for_response_file(similar_problem_response_path)
            TestingFactory.remove_response(similar_problem_response_path)

            # generate delay due to technician adding the solution
            # time.sleep(technician_delay)

            # Generate update for solved repository indicating the solution adopted for the problem
            TestingFactory.generate_update_repository(repository_update_path, index, problem)

            # generate delay due to user usage (between each request)
            # time.sleep(user_delay)

        # evaluate elapsed time and return it
        ending_time = datetime.datetime.now().timestamp()
        return ending_time - starting_time  # + technician_delay + user_delay

    @staticmethod
    def generate_problem_req_file(req_path, index, problem):
        """
           Simulate the request for a solution from the user.
           Basically it generates the same file that the Technical Support System
           would create after the user submits a new Problem Description.
           The creation of this file will trigger the activation of the
           troubleshooting procedure.
           :param req_path: indicates folder where the request file should be created
           :type req_path: string
           :param index: problem id of the simulated user's request
           :type index: integer
           :param problem: problem description of the simulated user's request
           :type problem : string
           :return: None
        """

        req_data = {
            "requests": [
                {
                    "requestID": index,
                    "problemDescription": problem
                }
            ]
        }
        dump_json(req_data, req_path)

    @staticmethod
    def remove_response(resp_path):
        """
           Simulate the user reading the advised solutions from the troubleshooting
           system by removing its output file
           :param resp_path: indicates path of the response file from the troubleshooting
                system
           :type resp_path: string
           :return: false if no response file is found
           :rtype: boolean
        """
        if os.path.exists(resp_path):
            os.remove(resp_path)
            return True

        print("An error in the pipeline occurred")
        return False

    @staticmethod
    def generate_update_repository(update_path, index, problem):
        """
           Simulate the file created by the technician where the solution for
           a specific problem is indicated. Used by the repository system to
           update its DB.
           :param update_path: indicates folder where the update file should be created
           :type update_path: string
           :param index: problem id of the simulated user's request
           :type index: integer
           :param problem: problem description of the simulated user's request
           :type problem : string
           :return: None
        """
        update_data = load_json(update_path)
        solution_records = list(update_data['records'])
        new_solution = {
            "problemDescription": problem,
            "solutionDescription": "dummy_solution",
            "isSolutionManual": False,
            "solutionIndex": index,
            "totalPresentedSolutions": 3
        }
        solution_records.append(new_solution)
        dump_json(update_data, update_path)

    @staticmethod
    def wait_for_response_file(similar_problem_response_path):
        """
           After sending the request to the troubleshooting system, wait for
           the creation of a new response file.
           :param similar_problem_response_path: indicates path of the response file
           :type similar_problem_response_path: string
           :return: None
        """
        while not os.path.exists(similar_problem_response_path):
            time.sleep(1)

    @staticmethod
    def populate_repository(data_set):
        """
        Populate the repository with a dummy dataset
        :param data_set: the csv file
        containing a set of problem_description,solution_description rows
        :return: None
        """
        ingestion_config = load_json("./solved_problems_repo/json/ingestionConfig.json")
        config_schema = load_json("./solved_problems_repo/json/schemas/ingestionConfigSchema.json")
        if not validate_json(ingestion_config, config_schema):
            print("Error: could not validate ingestionConfig.json format")
            return
        mongo_url = ingestion_config["mongodbURL"]
        repo_manager = RepositoryManager(mongo_url)
        if not repo_manager.is_connected():
            print("Error: could not connect to mongoDB cluster")
            return

        # open data_set and add problems to repo
        read_csv(data_set, lambda row: repo_manager.add_problem(row[0], row[1]))

        repo_manager.close()

    @staticmethod
    def test_non_elasticity_submission_pipeline(
            loads,
            output="./testing/csv/non_elasticity_troubleshooting.csv"):
        """
               Perform the submission pipeline under different loads and collect the timing
               results in an output file
               :param loads: The list of problems to submit to the system
               :param output: The output filename
               :return: None
        """
        results = [TestingFactory.test_problem_submission_pipeline(load) for load in loads]

        out_data = np.column_stack((loads, results))

        dump_csv_array(out_data, output)

    @staticmethod
    def test_non_elasticity_training_pipeline(loads,
                                              output="./testing/csv/non_elasticity_training.csv"):
        """
        Perform the training pipeline under different loads and collect the timing
        results in an output file
        :param loads: The list of workloads (ingestion records number) to test
        :param output: The output filename
        :return: None
        """
        results = [TestingFactory.test_training_pipeline(load) for load in loads]

        out_data = np.column_stack((loads, results))

        dump_csv_array(out_data, output)
