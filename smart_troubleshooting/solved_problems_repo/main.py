"""
This module contains the main function of the application.
It instantiates a task manager and launches
the required periodic daemons to make the repository work

Author: Leonardo Bacciottini
"""
from smart_troubleshooting.solved_problems_repo.repository_service \
    import RepositoryService

if __name__ == '__main__':
    scheduler = RepositoryService()
    scheduler.schedule_periodic_ingestion()
    scheduler.schedule_periodic_request_handler()
    scheduler.schedule_periodic_solved_problems_handler()
