"""
This module contains the main function of the application.
It instantiates a task manager and launches
the required periodic daemons to make the repository work
"""
from smart_troubleshooting.solved_problems_repo.scheduled_tasks_manager \
    import ScheduledTasksManager

if __name__ == '__main__':
    scheduler = ScheduledTasksManager(30, 10, 1)
