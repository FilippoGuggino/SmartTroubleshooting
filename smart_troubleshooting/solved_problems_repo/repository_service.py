"""
This module contains only the class RepositoryService.
Its purpose is to provide a scheduled executor service which periodically
launches three different services.

Author: Leonardo Bacciottini
"""

import threading
from datetime import datetime


from smart_troubleshooting.file_io import load_json, dump_json, validate_json
from smart_troubleshooting.solved_problems_repo.repository_manager import RepositoryManager


class RepositoryService:
    """
    This class realizes a task executor which periodically launches three jobs (independently):
    1. handle_new_problems: to add new problems to the repository
    2. handle_solution_requests: to reply to incoming requests for solutions
    3. activate_ingestion_procedure: to rebuild and replace the ingestion data set
    given some configurations stored in IngestionConfig.json.
    The three tasks can also be run on demand by using the API offered by this class
    """
    # pylint: disable=too-many-instance-attributes
    # Ten is reasonable in this case, since it is the number of I/O files

    # configuration file
    __config_filename = "./solved_problems_repo/json/IngestionConfig.json"

    # configuration schema
    __config_schema_name = "./solved_problems_repo/json/schemas/IngestionConfigSchema.json"

    # I/O files declaration
    __report_filename = None
    __ingestion_filename = None

    __req_filename = None
    __resp_filename = None
    __requests_schema_name = None
    __responses_schema_name = None

    __new_records_filename = None
    __perf_report_filename = None
    __new_records_schema_name = None
    __perf_report_schema_name = None

    def __init__(self):
        self.__load_configuration()  # ensure I/O filenames are loaded

    def __set_io_files(self, configuration):
        """
        Set I/O file names given a configuration.
        :param configuration: the configuration dictionary.
        :return: None
        """
        if configuration is not None:

            input_dir = configuration["input_directory"]
            output_dir = configuration["output_directory"]
            schema_dir = configuration["json_schemas_directory"]

            self.__report_filename = output_dir + "IngestionReport.json"
            self.__ingestion_filename = output_dir + "IngestionRecordsFile.json"

            self.__req_filename = input_dir + "SolutionRequestsFile.json"
            self.__resp_filename = output_dir + "SolutionResponsesFile.json"
            self.__requests_schema_name = schema_dir + "SolutionRequestsFileSchema.json"
            self.__responses_schema_name = schema_dir + "SolutionResponsesFileSchema.json"

            self.__new_records_filename = input_dir + "NewRecordsFile.json"
            self.__perf_report_filename = output_dir + "PerformanceReportFile.json"
            self.__new_records_schema_name = schema_dir + "NewRecordsFileSchema.json"
            self.__perf_report_schema_name = schema_dir + "PerformanceReportFileSchema.json"

    def __load_configuration(self):
        config_json = load_json(self.__config_filename)
        config_schema = load_json(self.__config_schema_name)
        if not validate_json(config_json, config_schema):
            print("Error: could not validate ingestionConfig.json format")
            return None
        self.__set_io_files(config_json)  # each time conf is loaded, update I/O files path
        return config_json

    def __load_repo_url(self):
        configuration = self.__load_configuration()
        if configuration is None:
            print("Error: could not validate configuration file")
            return None

        return configuration["mongodbURL"]

    def handle_solution_requests(self):
        """
        Parse SolutionRequestsFile.json.
        Process all requests and save responses in SolutionResponsesFile.json
        """
        # print("solution requests started")

        requests_schema = load_json(self.__requests_schema_name)
        responses_schema = load_json(self.__responses_schema_name)
        requests_json = load_json(self.__req_filename)

        if not validate_json(requests_json, requests_schema):
            print("Error: could not validate SolutionRequests.json format")
            return

        # get responses file so that we can append data
        responses_json = load_json(self.__resp_filename)
        if not validate_json(responses_json, responses_schema):
            print("Error: could not validate SolutionResponses.json format")
            return

        mongo_url = self.__load_repo_url()

        repo_manager = RepositoryManager(mongo_url)
        if not repo_manager.is_connected():
            return

        for request in requests_json["requests"]:
            solution = repo_manager.get_solution(request["problemID"])
            if solution is not None:
                response = {
                    "requestID": request["requestID"],
                    "responseType": "OK",
                    "solutionDescription": solution
                }
            else:
                response = {
                    "requestID": request["requestID"],
                    "responseType": "ERROR",
                }

            # append this last response to responses array
            responses_json["responses"].append(response)

        repo_manager.close()

        # dump this last version of responses file
        dump_json(responses_json, self.__resp_filename)

        # reinitialize requests file
        init_requests_json = {
            "requests": []
        }
        dump_json(init_requests_json, self.__req_filename)

    def handle_new_solved_problems(self):
        """
        Parse NewRecordsFile.json. Add parsed records to the repository and produce a report in
        PerformanceReportFile.json.
        """

        # print("new solved problems handler started")

        new_records_json = load_json(self.__new_records_filename)
        input_schema = load_json(self.__new_records_schema_name)
        if not validate_json(new_records_json, input_schema):
            print("Error: could not validate NewRecordsFile.json format")
            return

        output_json = load_json(self.__perf_report_filename)
        output_schema = load_json(self.__perf_report_schema_name)
        if not validate_json(output_json, output_schema):
            print("Error: could not validate PerformanceReportFile.json format")
            return
        reports = output_json["reports"]

        mongo_url = self.__load_repo_url()

        repo_manager = RepositoryManager(mongo_url)
        if not repo_manager.is_connected():
            return

        for record in new_records_json["records"]:
            print("adding problem: " + record["problemDescription"])
            repo_manager.add_problem(record["problemDescription"], record["solutionDescription"])
            report = {
                "isSolutionManual": record["isSolutionManual"],
                "totalPresentedSolutions": record["totalPresentedSolutions"]
            }
            if not record["isSolutionManual"]:
                report["solutionIndex"] = record["solutionIndex"]
            else:
                report["solutionIndex"] = -1

            reports.append(report)

        repo_manager.close()

        # dump new state of performance report file
        dump_json(output_json, self.__perf_report_filename)

        # reinitialize new records file
        init_records_json = {
            "records": []
        }
        dump_json(init_records_json, self.__new_records_filename)

    def activate_ingestion_procedure(self):
        """
        Read IngestionConfig.json to get configuration filters.
        Build a new ingestion dataset based on these filters.
        Save the outcome in IngestionRecordsFile.json
        """

        # print("ingestion procedure started")

        config_json = self.__load_configuration()
        if config_json is None:  # could not validate configuration file
            report = {
                "numberOfRecords": 0,
                "lastIngestionTime": str(datetime.now()),
                "exitStatus": "ERROR",
                "errorMessage": "Configuration file is bad formed"
            }
            # dump new state on report file
            dump_json(report, self.__report_filename)
            return

        output_json = {
            "records": []
        }
        ingestion_records = output_json["records"]

        mongo_url = config_json["mongodbURL"]

        repo_manager = RepositoryManager(mongo_url)
        if not repo_manager.is_connected():
            return

        result = repo_manager.get_ingestion_records(
            config_json["maxProblemAge"],
            config_json["maxNumberOfRecords"],
            config_json["bannedKeywords"])

        total = 0

        for record in result:
            record = {
                "problem_id": str(record["_id"]),
                "problemDescription": record["description"],
                "solution_id": str(record["solution_id"])
            }
            total += 1
            ingestion_records.append(record)

        repo_manager.close()

        # dump new state of ingestion file
        dump_json(output_json, self.__ingestion_filename)

        # build report
        report = {
            "numberOfRecords": total,
            "lastIngestionTime": str(datetime.now()),
        }
        if total < config_json["minNumberOfRecords"]:
            report["exitStatus"] = "ERROR"
            report["errorMessage"] = "Not enough eligible records"
        else:
            report["exitStatus"] = "OK"
        dump_json(report, self.__report_filename)

    def schedule_periodic_ingestion(self):
        """
        Schedule the ingestion procedure endlessly
        with a period found in "ingestionConfig.json" file
        """
        self.activate_ingestion_procedure()

        # we need the period from the configuration file
        configuration = self.__load_configuration()
        if configuration is None:
            period = 120  # after 120 seconds try again
        else:
            period = configuration["ingestionProcedurePeriod"]

        threading.Timer(period,  # re-init timer
                        self.schedule_periodic_ingestion).start()

    def schedule_periodic_request_handler(self):
        """
        Schedule the request handler task endlessly
        with a period specified in "ingestionConfig.json"
        :return: None
        """
        self.handle_solution_requests()

        # we need the period from the configuration file
        configuration = self.__load_configuration()
        if configuration is None:
            period = 120  # after 120 seconds try again
        else:
            period = configuration["solutionRequestsHandlerPeriod"]

        threading.Timer(period,  # re-init timer
                        self.schedule_periodic_request_handler).start()

    def schedule_periodic_solved_problems_handler(self):
        """
        Schedule the new solved problems handler task endlessly
        with a period specified in "ingestionConfig.json"
        :return: None
        """
        self.handle_new_solved_problems()

        # we need the period from the configuration file
        configuration = self.__load_configuration()
        if configuration is None:
            period = 120  # after 120 seconds try again
        else:
            period = configuration["newProblemsHandlerPeriod"]

        threading.Timer(period,  # re-init timer
                        self.schedule_periodic_solved_problems_handler).start()
