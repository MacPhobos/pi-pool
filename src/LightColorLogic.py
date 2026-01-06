import logging
from threading import Thread
from time import sleep
from queue import Queue, Empty


class LightColorLogic:

    RESET_COLOR_ID = 1000

    """
# 1. Show - Fast Color Wash
# 2. Fixed - Deep Blue Sea
# 3. Fixed - Royal Blue
# 4. Fixed - Afternoon Skies
# 5. Fixed - Aqua Green
# 6. Fixed - Emerald
# 7. Fixed - Cloud White
# 8. Fixed - Warm Red
# 9. Fixed - Flamingo
# 10. Fixed - Vivid Violet
# 11. Fixed - Sangria
# 12. Show - Slow Color Wash
# 13. Show - Blue/Cyan/White Fade
# 14. Show - Blue/Green/Magenta Fade
# 15. Show - Red/White/Blue Switch
# 16. Show - Fast Random Fade - Mardi Gras
# 17. Show - Fast Random Fade - Cool Cabaret
    """

    colors = {
        0:  {'id': 0,  'type': 'show',  'name': 'Fast Color Wash'},
        1:  {'id': 1,  'type': 'fixed', 'name': 'Deep Blue Sea'},
        2:  {'id': 2,  'type': 'fixed', 'name': 'Royal Blue'},
        3:  {'id': 3,  'type': 'fixed', 'name': 'Afternoon Skies'},
        4:  {'id': 4,  'type': 'fixed', 'name': 'Aqua Green'},
        5:  {'id': 5,  'type': 'fixed', 'name': 'Emerald'},
        6:  {'id': 6,  'type': 'fixed', 'name': 'Cloud White'},
        7:  {'id': 7,  'type': 'fixed', 'name': 'Warm Red'},
        8:  {'id': 8,  'type': 'fixed', 'name': 'Flamingo'},
        9:  {'id': 9,  'type': 'fixed', 'name': 'Vivid Violet'},
        10: {'id': 10, 'type': 'fixed', 'name': 'Sangria'},
        11: {'id': 11, 'type': 'show',  'name': 'Slow Color Wash'},
        12: {'id': 12, 'type': 'show',  'name': 'Blue/Cyan/White Fade'},
        13: {'id': 13, 'type': 'show',  'name': 'Blue/Green/Magenta Fade'},
        14: {'id': 14, 'type': 'show',  'name': 'Red/White/Blue Switch'},
        15: {'id': 15, 'type': 'show',  'name': 'Fast Random Fade - Mardi Gras'},
        16: {'id': 16, 'type': 'show',  'name': 'Fast Random Fade - Cool Cabaret'}
    }

    def __init__(self, light):
        self.colorCount = 17
        self.lightSwitchDelay = 1.3
        self.secondsToWaitForWhiteLightAfter60sOff = 17
        self.secondsToWaitBetweenColorSwitches = 1.2
        self.RESET_SYNCHRONIZATION_DELAY = 12

        self.light = light
        self.keepRunning = True
        self.isLightPositionKnown = False
        self.currentColorId = 0

        self.command_queue = Queue()
        self.interrupt_requested = False
        self.is_processing = False
        self.startThread()

    def stop(self):
        self.keepRunning = False
        self.interrupt_requested = True
        self.thread.join()

    def startThread(self):
        self.thread = Thread(target=self.task)
        self.thread.daemon = True
        self.thread.start()

    def task(self):
        logging.info('LightColorLogic: Starting...')
        while self.keepRunning:
            try:
                # Wait for a command
                command, *args = self.command_queue.get(timeout=1)

                # Check interrupt AFTER getting command, before processing
                if self.interrupt_requested:
                    logging.info("LightColorLogic - command skipped due to interrupt")
                    self.interrupt_requested = False
                    self.command_queue.task_done()
                    continue

                self.is_processing = True
                logging.info(f"LightColorLogic - processing command: {command}")

                if command == 'reset':
                    self.__doResetToFirstColor()
                elif command == 'next':
                    self.__doNextColor()
                elif command == 'set':
                    self.__doSetColor(args[0])

                self.is_processing = False
                self.command_queue.task_done()

            except Empty:
                self.is_processing = False
                continue

    def resetToFirstColor(self):
        self.command_queue.put(('reset',))

    """
    OPERATING THE LIGHT
Your Hayward ColorLogic light is operated through power-cycling: a
method of changing modes which requires no special controller or
interface. To activate the light, simply turn on the switch. To deactivate
the light, turn off the switch. To advance to the next program, turn the
switch off, then back on within 10 seconds. Whenever the light has
been off for over 60 seconds, and is first turned on, it will come on to
white for 15 seconds for quick clear view of your pool, then go to the
last fixed color or color show it was running.

LIGHT SYNCHRONIZATION
If your pool or spa has multiple Hayward ColorLogic LED lights, they
may be operated independently, or they can be easily synchronized so
they will all display the same colors and shows at the same time. For
light synchronization, all lights must be wired to the same switch. Once
installed, all lights should be automatically synchronized, however, if
they get out of sync, they can be re-synchronized easily. To re-synchronize 
your lights, turn the switch on, then back off, then wait between 11 and 14 
seconds and turn the switch back on. When the lights
come back on, they should enter program #1, and be synchronized.
    """

    def __doResetToFirstColor(self):
        logging.info("LightColorLogic: Resetting to first color")
        self.light.off()
        sleep(self.secondsToWaitBetweenColorSwitches)
        if self.interrupt_requested: return
        self.light.on()
        sleep(self.secondsToWaitForWhiteLightAfter60sOff)   # wait for possible white light on for 15s after 60s of being off
        if self.interrupt_requested: return
        self.light.off()
        sleep(self.RESET_SYNCHRONIZATION_DELAY)   # wait 11 to 14s to reset to color 0
        if self.interrupt_requested: return
        self.light.on()
        self.isLightPositionKnown = True
        self.currentColorId = 0
        sleep(self.lightSwitchDelay)
        logging.info("LightColorLogic: Resetting to first color - DONE")

    def __doNextColor(self):
        self.light.off()
        sleep(self.secondsToWaitBetweenColorSwitches)
        self.light.on()

    def __doSetColor(self, colorId: int):

        logging.info("LightColorLogic - __doSetColor " + str(colorId))

        if self.isLightPositionKnown is False or colorId == self.RESET_COLOR_ID:
            self.__doResetToFirstColor()
            if self.interrupt_requested: return
            if colorId == self.RESET_COLOR_ID:
                colorId = 0

        secondsInOffState = self.light.secondsInOffState()
        if secondsInOffState is not None and secondsInOffState > 60:
            logging.info("LightColorLogic - light has been off for 60s - waiting for white check color to go away")
            self.light.on()
            sleep(self.secondsToWaitForWhiteLightAfter60sOff)
            if self.interrupt_requested: return

        if self.currentColorId == colorId:
            logging.info("LightColorLogic - at color " + str(colorId))
            return

        while self.currentColorId != colorId:
            if not self.keepRunning or self.interrupt_requested:
                logging.info("LightColorLogic - stopping color set")
                break
            logging.info("LightColorLogic - doColorSet - currentColorId: " + str(self.currentColorId) + " target colorId: " + str(colorId))
            self.light.off()
            sleep(self.lightSwitchDelay)
            self.light.on()
            sleep(self.lightSwitchDelay)
            self.currentColorId = (self.currentColorId + 1) % self.colorCount

        logging.info("LightColorLogic - doColorSet - currentColorId: " + str(self.currentColorId) + " - " + self.getCurrentColorName())

    def hardStop(self):
        """Immediately stops any running command and clears the command queue."""
        logging.info("LightColorLogic - hardStop called")
        self.interrupt_requested = True
        with self.command_queue.mutex:
            self.command_queue.queue.clear()

    def nextColor(self):
        self.command_queue.put(('next',))

    def setColor(self, colorId):
        if not isinstance(colorId, int) or not 0 <= colorId < self.colorCount:
            logging.warning(f"LightColorLogic - invalid colorId: {colorId}")
            return
        self.command_queue.put(('set', colorId))

    def getCurrentColorName(self):
        if self.isLightPositionKnown is False:
            return "Unknown"
        color = self.colors.get(self.currentColorId)
        return color["name"]

    def setColorMessageHandler(self, data):
        if self.is_processing or self.command_queue.qsize() > 0:
            logging.info("LightColorLogic - setColorMessageHandler - to " + str(data) + " - SKIPPING. A command is active or queued.")
            return

        logging.info("LightColorLogic - setColorMessageHandler to " + str(data))
        try:
            color_id = int(data)
            self.setColor(color_id)
        except (ValueError, TypeError):
            logging.warning(f"LightColorLogic - invalid data for setColorMessageHandler: {data}")

    def dump(self):
        logging.info("LightColorLogic - isLightPositionKnown: " + str(self.isLightPositionKnown))
        logging.info("LightColorLogic - currentColorId: " + str(self.currentColorId) + " - " + self.getCurrentColorName())
