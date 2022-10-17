"""
Author: Leonardo Bacciottini
"""
from smart_troubleshooting.testing.testing_factory import TestingFactory

if __name__ == '__main__':
    # loads = range(5, 310, 10)
    # TestingFactory.test_non_elasticity_training_pipeline(loads)
    # TestingFactory.test_training_pipeline(300)
    loads = range(1, 10, 1)
    TestingFactory.test_non_elasticity_submission_pipeline(loads)
