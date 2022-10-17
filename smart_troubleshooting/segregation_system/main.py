"""
This module contains the main function that will start the Segregation task service
"""
from smart_troubleshooting.segregation_system.pd_segregation_system\
    import PDSegregationSystem

if __name__ == '__main__':
    segregation_system = PDSegregationSystem()
    segregation_system.schedule_periodic_activation()
