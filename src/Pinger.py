import logging
import time

from threading import Thread


class Pinger:

    def __init__(self, config, networkMonitor=None):
        from hal.interfaces import INetworkMonitor

        self.allGood = True
        self.config = config
        self.keepRunning = True

        if networkMonitor is None:
            # Backward compatibility
            from hal import HardwareFactory
            factory = HardwareFactory(config.getHardwareMode())
            self.networkMonitor = factory.createNetworkMonitor()
        else:
            self.networkMonitor = networkMonitor

        self.startThread()

    def startThread(self):
        self.pingerThread = Thread(target=self.task)
        self.pingerThread.daemon = True
        self.pingerThread.start()

    def task(self):
        logging.info('Pinger: Starting...')
        while self.keepRunning:
            self.allGood = self.networkMonitor.ping(self.config.pingTarget, count=10, interval=1)

            # Check keepRunning flag multiple times between ping batches
            # This allows for prompt shutdown (checks every 10 seconds instead of 240)
            for _ in range(23):  # 23 more checks to reach ~240 seconds total
                if not self.keepRunning:
                    logging.info('Pinger: Stopping...')
                    return
                time.sleep(10)

        logging.info('Pinger: Stopped')

    def stop(self):
        """Gracefully stop the pinger thread"""
        logging.info('Pinger: Stop requested')
        self.keepRunning = False

    def isConnected(self):
        return self.allGood
