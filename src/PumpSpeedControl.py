import logging

from RelayBlock import RelayBlock
from PumpSpeed import PumpSpeed
from Config import Config


class PumpSpeedControl:

    def __init__(self, relayBlock: RelayBlock):
        config = Config.getInstance()

        self.relayBlock = relayBlock

        self.relayPorts = {
            PumpSpeed.S1: config.pumpSpeedS1Port,
            PumpSpeed.S2: config.pumpSpeedS2Port,
            PumpSpeed.S3: config.pumpSpeedS3Port,
            PumpSpeed.S4: config.pumpSpeedS4Port
        }

    def setSpeed(self, speed: PumpSpeed):
        self.clearSpeeds()
        logging.info("PumpSpeedControl - Set speed: " + speed.value)
        self.relayBlock.portOn(self.relayPorts[speed])

    def clearSpeeds(self):
        for port in self.relayPorts:
            self.relayBlock.portOff(port)
