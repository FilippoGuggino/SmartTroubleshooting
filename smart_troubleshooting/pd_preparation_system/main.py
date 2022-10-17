"""
This module provides an interface to the engineer for testing purposes.

Author: Filippo Guggino
"""

from smart_troubleshooting.pd_preparation_system.pd_preparation_system_service \
    import PDPreparationSystemService

if __name__ == '__main__':
    preparation_service = PDPreparationSystemService()
    preparation_service.schedule_preparation_procedure()
