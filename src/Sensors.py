
import json


class Sensors:

    def __init__(self):
        self.sensors = []
        return 
    
    def addSensor(self, sensor):
        self.sensors.append(sensor)
        
    def collectSensorStatus(self):
        message = {}
        
        for sensor in self.sensors:
            message.update(sensor.status())

        return message

    def getMQTTMessage(self):
        return json.dumps(self.collectSensorStatus())

    def getSensor(self, sensorName):
        for sensor in self.sensors:
            if sensor.getName() == sensorName:
                return sensor
        return None

    def logSensorsToDb(self):
        for sensor in self.sensors:
            sensor.logSensorToDb()
