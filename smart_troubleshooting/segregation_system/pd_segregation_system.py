"""
This module contains only one class, providing an API to perform the segregation
procedure on a list of problems, retrieved from an input file.
"""

import math
import threading
from datetime import datetime
import random

from smart_troubleshooting.file_io \
    import load_json, validate_json, dump_json, dump_csv


class PDSegregationSystem:
    """
    This class implements the Segregation procedure of records ingested to train the NN.
    In particular, it will generate the three test,
    training and validation sets basing on configurations
    in segregationConfig.json
    """

    # I/O files
    __ingestion_records_file = "../solved_problems_repo/json/IngestionRecordsFile.json"
    __segregation_config_file = "json/segregationConfig.json"
    __test_set_file = "csv/testSet.csv"
    __training_set_file = "csv/trainingSet.csv"
    __validation_set_file = "csv/validationSet.csv"
    __segregation_report_file = "json/segregationReport.json"
    __problem_mapping_file = "csv/ProblemMappingFile.csv"

    # json schemas
    __ingestion_records_schema = "json/schemas/IngestionRecordsFileSchema.json"
    __segregation_config_schema = "json/schemas/segregationConfigSchema.json"

    def __load_configuration(self):
        """
        Load the configuration file and return its json.
        :return: The json configuration in case of success.
        None if the configuration file was bad formed.
        """

        configuration = load_json(self.__segregation_config_file)
        configuration_schema = load_json(self.__segregation_config_schema)

        good_format = validate_json(configuration, configuration_schema)

        if not good_format:
            return None

        # check if the three percentages in the file correctly sum to 100
        total_percent = \
            configuration["testPercent"] + \
            configuration["trainingPercent"] + \
            configuration["validationPercent"]

        if total_percent != 100:
            return None
        return configuration

    def __load_records(self):
        """
        Load the ingestion records file and return its json.
        :return: The inner records list in case of success. None if the file was bad formed.
        """

        records = load_json(self.__ingestion_records_file)
        records_schema = load_json(self.__ingestion_records_schema)

        good_format = validate_json(records, records_schema)

        if not good_format:
            return None
        return records["records"]

    @staticmethod
    def __assign_problem_ids(problems):
        """
        Assign an integer identifier ("problem_id") field to each problem
        :param problems: an array of json problem descriptors.
        Thought to be "__load_records" result.
        """
        for i, problem in enumerate(problems, start=1):
            problem["problem_id"] = i

    def __write_problem_id_description(self, problems):
        """
        Write output file for Preparation System,
        containing a csv list of problem ids and descriptions.
        :param problems: The list of problems to be written.
        """

        head_row = ["problem id", "problem description"]
        columns = ["problem_id", "problemDescription"]
        dump_csv(head_row, problems, self.__problem_mapping_file, columns)

    def __write_sets(self, problems, configuration):
        """
        Write the three file test,validation and training set filling
        them with random elements extracted from the list of passed problems,
        according to the percentages written in configuration file
        :param problems: The list of problems to be extracted.
        :param configuration: File in which percentages are written
        :return: None
        """
        training_records = self.__self_join(problems)

        # shuffle randomly the items
        random.shuffle(training_records)
        random.shuffle(training_records)

        index_training = math.floor(len(training_records) * configuration["trainingPercent"] / 100)
        index_validation = math.floor(len(training_records)
                                      * configuration["validationPercent"] / 100)
        # index_test = len(training_records) - index_training - index_validation

        training_set = training_records[:index_training]
        validation_set = training_records[index_training:index_training + index_validation]
        test_set = training_records[index_training + index_validation:]

        if len(training_set) > 0:
            head_row = training_set[0].keys()
        else:
            return

        dump_csv(head_row, training_set, self.__training_set_file)
        dump_csv(head_row, validation_set, self.__validation_set_file)
        dump_csv(head_row, test_set, self.__test_set_file)

    def __write_report(self, exit_status, error_message=None):

        report_json = {"exitStatus": exit_status,
                       "errorMessage": error_message,
                       "lastSegregationTime": str(datetime.now())}

        dump_json(report_json, self.__segregation_report_file)

    @staticmethod
    def __self_join(problems):  # to be used in "__write_sets"
        json_data_list = []
        for problem_left in problems:
            for problem_right in problems:
                if problem_left["problem_id"] == problem_right["problem_id"]:
                    continue
                same_solution = problem_left["solution_id"] == problem_right["solution_id"]
                object_json = {"problem_1_id": problem_left["problem_id"],
                               "problem_2_id": problem_right["problem_id"],
                               "same_solution": 1 if same_solution else 0}
                json_data_list.append(object_json)

        # print(json.dumps(json_data_list, indent=2))

        return json_data_list

    def activate_segregation_procedure(self):
        """
        Activate the segregation procedure and split ingestion records in three sets
        ready to train the NN.
        """

        print("starting segregation")

        configuration = self.__load_configuration()
        if configuration is None:
            self.__write_report("ERROR", error_message="Configuration file is bad formed")
            return

        problems = self.__load_records()
        if problems is None:
            self.__write_report("ERROR", error_message="Records input file is bad formed")
            return

        self.__assign_problem_ids(problems)  # now problems have also "problem_id" field
        self.__write_problem_id_description(problems)

        self.__write_sets(problems, configuration)
        self.__write_report("OK")

    def schedule_periodic_activation(self):
        """
        Schedule the segregation procedure endlessly
        with a period found in "segregationConfig.json" file
        """
        self.activate_segregation_procedure()

        # we need the period from the configuration file
        configuration = self.__load_configuration()
        if configuration is None:
            self.__write_report("ERROR", error_message="Configuration file is bad formed")
            return

        period = configuration["segregationPeriod"]

        threading.Timer(period,  # re-init timer
                        self.schedule_periodic_activation).start()
