class RpiTemperature:

    def __init__(self, cpuMonitor=None):
        from hal.interfaces import ICpuMonitor

        if cpuMonitor is None:
            # Backward compatibility
            from Config import Config
            from hal import HardwareFactory
            config = Config.getInstance()
            factory = HardwareFactory(config.getHardwareMode())
            self.cpuMonitor = factory.createCpuMonitor()
        else:
            self.cpuMonitor = cpuMonitor

    def status(self):
        status = {}
        status['temp_rpi'] = float("{0:.2f}".format(self.getCurrentTemp()))
        return status

    def getName(self):
        return "temp_rpi"

    def getCurrentReading(self):
        return self.getCurrentTemp()

    def getCurrentTemp(self):
        return self.cpuMonitor.getTemperature()
