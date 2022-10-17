"""
This file contains a script that launches the whole smart_troubleshooting service
"""
import time

from smart_troubleshooting.pd_preparation_system.pd_preparation_system_service import PDPreparationSystemService
from smart_troubleshooting.pd_similarity_dev_system.main import _main
from smart_troubleshooting.pd_similarity_dev_system.tests.test_main import MockArgs
from smart_troubleshooting.performance_monitoring_system.performance_monitoring_system import \
    PerformanceMonitoringSystem
from smart_troubleshooting.segregation_system.pd_segregation_system import PDSegregationSystem
from smart_troubleshooting.solved_problems_repo.repository_service import RepositoryService
from smart_troubleshooting.technical_support_system.main_menu import MainMenu
from smart_troubleshooting.troubleshooting_system.troubleshooting_system_service import TroubleShootingSystemService

if __name__ == '__main__':

    # repository
    scheduler = RepositoryService()
    scheduler.schedule_periodic_ingestion()
    scheduler.schedule_periodic_request_handler()
    scheduler.schedule_periodic_solved_problems_handler()

    time.sleep(1)

    # segregation
    segregation_system = PDSegregationSystem()
    segregation_system.schedule_periodic_activation()

    time.sleep(1)

    # preparation
    preparation_service = PDPreparationSystemService()
    preparation_service.schedule_preparation_procedure()

    time.sleep(1)

    # troubleshooting system
    troubleshooting_service = TroubleShootingSystemService()
    troubleshooting_service.schedule_troubleshooting_procedure()

    performanceMonitoringSystem = PerformanceMonitoringSystem()

    # GUI
    technical_sys = MainMenu()
    technical_sys.start_interface()

    while True:
        command = input("Type a command (\"accuracy\" or \"train\" or \"test\") > ")
        if command == "accuracy":
            performanceMonitoringSystem.compute_accuracy()
        elif command == "train":
            args = MockArgs("manual_train",
                            "./pd_similarity_dev_system/json/examples/manual_train_config.json")
            _main(args)
        elif command == "test":
            args = MockArgs("test",
                            "./pd_similarity_dev_system/json/examples/test_config.json")
            _main(args)
        else:
            print("Please type a valid command")

