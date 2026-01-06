import time
from DB import DB


class Sensor:
    
    def __init__(self, sensorDevice):
        self.device = sensorDevice
        self.db = DB.getInstance()
        self.lastDbLogTime = time.time()

    def status(self):
        return self.device.status()

    def getName(self):
        return self.device.getName()

    def getCurrentReading(self):
        return self.device.getCurrentReading()

    def logSensorToDb(self):
        if time.time() - self.lastDbLogTime > 60 * 5:
            self.db.logSensor(self.getName(), self.getCurrentReading())
            self.lastDbLogTime = time.time()
