from smart_troubleshooting.troubleshooting_system.troubleshooting_system_service \
    import TroubleShootingSystemService

if __name__ == '__main__':
    troubleshooting_service = TroubleShootingSystemService()
    troubleshooting_service.schedule_troubleshooting_procedure()
