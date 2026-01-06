from Config import Config


class RelayBlock:
    pins = [
        {'gpio': 25, 'name': 'GPIO 25', 'state': 'LOW', 'relay_port': 8, 'used': True},
        {'gpio': 23, 'name': 'GPIO 23', 'state': 'LOW', 'relay_port': 6, 'used': True},
        {'gpio': 24, 'name': 'GPIO 24', 'state': 'LOW', 'relay_port': 7, 'used': True},
        {'gpio': 22, 'name': 'GPIO 22', 'state': 'LOW', 'relay_port': 4, 'used': False},
        {'gpio': 27, 'name': 'GPIO 27', 'state': 'LOW', 'relay_port': 3, 'used': False},
        {'gpio': 17, 'name': 'GPIO 17', 'state': 'LOW', 'relay_port': 2, 'used': False},
        {'gpio': 18, 'name': 'GPIO 18', 'state': 'LOW', 'relay_port': 5, 'used': False},
        {'gpio': 4, 'name': 'GPIO  4', 'state': 'LOW', 'relay_port': 1, 'used': False},
    ]

    def __init__(self, gpioController=None):
        from hal.interfaces import IGpioController, PinMode, PinDirection, PinState

        self.config = Config.getInstance()
        self.dontSwitchDevices = self.config.noDevices

        # Use injected controller or create simulated one for backward compatibility
        if gpioController is None:
            # Backward compatibility: auto-create based on hardware mode
            from hal import HardwareFactory
            factory = HardwareFactory(self.config.getHardwareMode())
            self.gpio = factory.createGpioController()
        else:
            self.gpio = gpioController

        self.gpio.setMode(PinMode.BCM)
        self.initPorts()

    def initPorts(self):
        from hal.interfaces import PinDirection, PinState
        # Set each used pin as an output:
        for pin in self.pins:
            self.gpio.setup(pin["gpio"], PinDirection.OUT)
            self.gpio.output(pin["gpio"], PinState.HIGH)

    def pinOn(self, gpioPin):
        from hal.interfaces import PinState
        if self.dontSwitchDevices is True:
            return

        self.gpio.output(gpioPin, PinState.LOW)

    def pinOff(self, gpioPin):
        from hal.interfaces import PinState
        if self.dontSwitchDevices is True:
            return

        self.gpio.output(gpioPin, PinState.HIGH)

    def portOn(self, port):
        gpio = self.gpioFromPort(port)
        self.pinOn(gpio)

    def portOff(self, port):
        gpio = self.gpioFromPort(port)
        self.pinOff(gpio)

    def gpioFromPort(self, port):
        for pin in self.pins:
            if pin["relay_port"] == port:
                return pin["gpio"]
