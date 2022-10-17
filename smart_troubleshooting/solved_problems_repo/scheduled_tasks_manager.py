"""
This module contains only the class ScheduledTasksManager.
Its purpose is to provide a scheduled executor service which periodically
launches three different services.
"""

import threading
from datetime import datetime

from smart_troubleshooting.solved_problems_repo.repository_manager \
    import RepositoryManager
from smart_troubleshooting.file_io import load_json, dump_json, validate_json


class ScheduledTasksManager:  # pylint: disable=too-few-public-methods
    """
    This class realizes a task executor which periodically launches three jobs (independently):
    1. handle_new_problems: to add new problems to the repository
    2. handle_solution_requests: to reply to incoming requests for solutions
    3. activate_ingestion_procedure: to rebuild and replace the ingestion data set
    given some configurations stored in IngestionConfig.json
    """

    def __init__(self,
                 ingestion_period,
                 handle_new_problems_period,
                 handle_solution_requests_period):
        """
        constructor of this class
        :param ingestion_period: The initial value of ingestion procedure period (in seconds).
        From the second execution of the procedure, it will be taken from the configuration file
        :param handle_new_problems_period: The period of new problems handler
        procedure (in seconds)
        :param handle_solution_requests_period: The period of solution requests handler
        procedure (in seconds). It should be lower than the other periods
        because its outcome will be used by Technical Support System
        """
        self.handle_solution_requests_period = handle_solution_requests_period
        self.handle_new_solved_problems_period = handle_new_problems_period
        self.initial_ingestion_period = ingestion_period
        self.__initialize_timers()

    def __handle_solution_requests(self):
        """
        Parse SolutionRequestsFile.json.
        Process all requests and save responses in SolutionResponsesFile.json
        """
        print("solution requests started")

        req_filename = "json/SolutionRequestsFile.json"
        resp_filename = "json/SolutionResponsesFile.json"
        requests_schema_name = "./json/schemas/SolutionRequestsFileSchema.json"
        responses_schema_name = "./json/schemas/SolutionResponsesFileSchema.json"
        requests_json = load_json(req_filename)
        requests_schema = load_json(requests_schema_name)
        responses_schema = load_json(responses_schema_name)

        if not validate_json(requests_json, requests_schema):
            print("Error: could not validate SolutionRequests.json format")
            return

        # get responses file so that we can append data
        responses_json = load_json(resp_filename)
        if not validate_json(responses_json, responses_schema):
            print("Error: could not validate SolutionResponses.json format")
            return

        repo_manager = RepositoryManager()

        for request in requests_json["requests"]:
            solution = repo_manager.get_solution(request["problemDescription"])
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
        dump_json(responses_json, resp_filename)

        # reinitialize requests file
        init_requests_json = {
            "requests": []
        }
        dump_json(init_requests_json, req_filename)

        # re-init timer
        threading.Timer(self.handle_solution_requests_period,
                        self.__handle_solution_requests).start()

    def __handle_new_solved_problems(self):
        """
        Parse NewRecordsFile.json. Add parsed records to the repository and produces a report in
        PerformanceReportFile.json.
        """

        print("new solved problems handler started")

        input_filename = "json/NewRecordsFile.json"
        output_filename = "json/PerformanceReportFile.json"
        input_schema_name = "./json/schemas/NewRecordsFileSchema.json"
        output_schema_name = "./json/schemas/PerformanceReportFileSchema.json"

        new_records_json = load_json(input_filename)
        input_schema = load_json(input_schema_name)
        if not validate_json(new_records_json, input_schema):
            print("Error: could not validate NewRecordsFile.json format")
            return

        output_json = load_json(output_filename)
        output_schema = load_json(output_schema_name)
        if not validate_json(output_json, output_schema):
            print("Error: could not validate PerformanceReportFile.json format")
            return
        reports = output_json["reports"]

        repo_manager = RepositoryManager()

        for record in new_records_json["records"]:
            repo_manager.add_problem(record["problemDescription"], record["solutionDescription"])
            report = {
                "isSolutionManual": record["isSolutionManual"],
                "totalPresentedSolutions": record["totalPresentedSolutions"]
            }
            if not record["isSolutionManual"]:
                report["solutionIndex"] = record["solutionIndex"]

            reports.append(report)

        repo_manager.close()

        # dump new state of performance report file
        dump_json(output_json, output_filename)

        # reinitialize new records file
        init_records_json = {
            "records": []
        }
        dump_json(init_records_json, input_filename)

        # re-init timer
        threading.Timer(self.handle_new_solved_problems_period,
                        self.__handle_new_solved_problems).start()

    def __activate_ingestion_procedure(self):
        """
        Read IngestionConfig.json to get configuration filters.
        Build a new ingestion dataset based on these filters.
        Save the outcome in IngestionRecordsFile.json
        """

        print("ingestion procedure started")

        config_filename = "json/IngestionConfig.json"
        report_filename = "json/IngestionReport.json"
        ingestion_filename = "json/IngestionRecordsFile.json"
        config_schema_name = "./json/schemas/IngestionConfigSchema.json"

        config_json = load_json(config_filename)
        config_schema = load_json(config_schema_name)
        if not validate_json(config_json, config_schema):
            print("Error: could not validate ingestionConfig.json format")
            report = {
                "numberOfRecords": 0,
                "lastIngestionTime": str(datetime.now()),
                "exitStatus": "ERROR",
                "errorMessage": "Configuration file is bad formed"
            }
            # dump new state on report file
            dump_json(report, report_filename)
            return

        output_json = {
            "records": []
        }
        ingestion_records = output_json["records"]

        repo_manager = RepositoryManager()

        result = repo_manager.get_ingestion_records(
            config_json["maxProblemAge"],
            config_json["maxNumberOfRecords"],
            config_json["bannedKeywords"])

        total = 0

        for record in result:
            record = {
                "problemDescription": record["description"],
                "solution_id": str(record["solution_id"])
            }
            total += 1
            ingestion_records.append(record)

        repo_manager.close()

        # dump new state of ingestion file
        dump_json(output_json, ingestion_filename)

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
        dump_json(report, report_filename)

        # re-init timer
        threading.Timer(config_json["ingestionProcedurePeriod"],
                        self.__activate_ingestion_procedure).start()

    def __initialize_timers(self):
        threading.Timer(self.initial_ingestion_period,
                        self.__activate_ingestion_procedure).start()
        threading.Timer(self.handle_new_solved_problems_period,
                        self.__handle_new_solved_problems).start()
        threading.Timer(self.handle_solution_requests_period,
                        self.__handle_solution_requests).start()
