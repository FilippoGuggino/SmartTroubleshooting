# Author: Federico Pacini
"""Module in charge of providing a singleton object to compute the performances of the related NN"""
import os.path

from smart_troubleshooting.file_io import validate_json, dump_json, set_attribute, load_json


def singleton(cls):
    """Decorator that will be used to implement a singleton patter"""
    instance = [None]

    def wrapper(*args, **kwargs):
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return wrapper


@singleton
class PerformanceMonitoringSystem:  # pylint: disable=too-few-public-methods
    """Offers a singleton object on which compute_accuracy method
    can be invoked to get an accuracy value of the NN

    Input file:
        PerformanceReportFile (from Solved Problem Repository System)

    Output file:
        AccuracyFile
    """
    PerformanceAccuracyFile = "./performance_monitoring_system/json/PerformanceAccuracyFile.json"
    AccuracyFile = "./performance_monitoring_system/json/AccuracyFile.json"
    StoredInfoAccuracyFile = "./performance_monitoring_system/" \
                             "json/StoredInfoAccuracyFile.json"  # since not using any DB

    PerformanceReportFile = "./solved_problems_repo/json/" \
                            "PerformanceReportFile.json"  # from Solved Problem Repository system
    PerformanceReportFileValidationSchema = "./performance_monitoring_system/" \
                                            "json/PerformanceReportFileValidationSchema.json"

    # Debugging method
    def __init__(self):
        print("Singleton created!")

        if not os.path.isfile(self.PerformanceAccuracyFile):
            print("PerformanceAccuracyFile not exist.. create")
            file_dict = {"accuracy_threshold": 1}
            dump_json(file_dict, self.PerformanceAccuracyFile)

        if not os.path.isfile(self.AccuracyFile):
            print("AccuracyFile not exist.. create")
            file_dict = {"accuracy": "?"}
            dump_json(file_dict, self.AccuracyFile)

        if not os.path.isfile(self.StoredInfoAccuracyFile):
            print("StoredInfoAccuracyFile not exist.. create")
            file_dict = {"partial_sum_of_scores": 0, "number_of_scores": 0}
            dump_json(file_dict, self.StoredInfoAccuracyFile)

    def compute_accuracy(self):
        """
        This method compute the accuracy on the smartTroubleshooting NN
        as the average sum of score on single records.
        The score on single record is so computed:
        total_solutions_presented_for_that_record = TOT
        position_of_record_in_presented_list = Pos

        Score = (TOT - Pos + 1) / TOT

        Extremes:
            if Pos == 1 -> score = 1 (first solution)
            if Pos == Tot -> score = 1/TOT (last solution)
            if manually_inserted_solution == true -> score = 0
        """
        # Read PerformanceReportFile and get scores
        reports_info = load_json(self.PerformanceReportFile)
        reports_info_schema = load_json(self.PerformanceReportFileValidationSchema)
        if reports_info is None:
            print("Not new reports: impossible to recompute the accuracy!")
            return
        validate_json(reports_info, reports_info_schema)
        # _validate_file(reports_info, reports_info_schema)
        number_of_new_scores = len(reports_info['reports'])

        # Compute sum of scores on new inserted
        new_partial_sum_of_score = 0
        for report_info in reports_info['reports']:

            if int(report_info["isSolutionManual"]) == 0:
                tot_presented_solution = int(report_info["totalPresentedSolutions"])
                sol_index = int(report_info["solutionIndex"])
                new_partial_sum_of_score += \
                    (tot_presented_solution - sol_index + 1) / tot_presented_solution

        # Compute the total sum
        # (partial_score in StoredInfoAccuracyFile + sum of scores on new inserted)
        stored_report_info = load_json(self.StoredInfoAccuracyFile)
        stored_sum_of_score = stored_report_info["partial_sum_of_scores"]
        new_sum_of_score = stored_sum_of_score + new_partial_sum_of_score
        total_number_of_scores = stored_report_info["number_of_scores"] + number_of_new_scores

        # Compute new accuracy
        # (total sum / (#new inserted scores + number_of_scores in StoredInfoAccuracyFile))
        accuracy = new_sum_of_score / total_number_of_scores

        print(accuracy)
        # Write it in AccuracyFile
        set_attribute(self.AccuracyFile, "accuracy", accuracy)

        # Write new_sum_of_score, total_number_of_scores in StoredInfoAccuracyFile
        set_attribute(self.StoredInfoAccuracyFile, "partial_sum_of_scores", new_sum_of_score)
        set_attribute(self.StoredInfoAccuracyFile, "number_of_scores", total_number_of_scores)

        # Empty PerformanceReportFile
        set_attribute(self.PerformanceReportFile, "reports", [])
