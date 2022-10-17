"""
This is a test main file
"""
# This is a sample Python script.

# Press Maiusc+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from smart_troubleshooting.performance_monitoring_system.performance_monitoring_system import \
    PerformanceMonitoringSystem

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Test singleton
    performanceMonitoringSystem = PerformanceMonitoringSystem()
    # Got the same singleton object with ->
    # performanceMonitoringSystem1 = PerformanceMonitoringSystem()
    performanceMonitoringSystem.compute_accuracy()
