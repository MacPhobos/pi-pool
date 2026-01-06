
# Description of hardware connections

This description is intended as a seed for diagram generation. We describe connections between various hardware components.

## Hardware connections

### Raspberry Pi (RPI)
 - needs a 3Amp power supply
 - needs SD card to store software
 - needs ethernet or wifi to connect to your local network

### 8 port relay module (RelayModule)
 - needs a dedicated 5V power supply. Do not power it using RPI 5V pin.
 - controlled by RPI
 - 5v pins from the RPI connect to RelayModule per port inputs to control the relay on/off operation
 - each relay controls a 1V to 220V **low aperage** circuit
 - never connect high amperate devices to this type of a relay. This is why we need the Contactor module capable of handling high amps.

### Pool Pump
 - power is switched on/off by a contactor module (PumpContactor) rated for correct voltage/amps (e.g. 110V/10A or 220V/5-10A)
 - the contactor module is controlled by an input from one of the relay ports on the RelayModule
 - the contactor control input for on/off control is connected to a port on RelayModule.

### Pool Heater
 - Hayward heaters provide on/off control using a 24V closed loop signal when in "bO" mode.
 - heaters of other brands may not provide this on/off signal.
 - the cable (two wires) coming from the heater is connected to the two power ports on RelayModule.
 - the RelayModule input from RPI will either close the loop to start the heater or open it to stop the heater.

### Pool Light
 - typically powered by a separate 110V or 220v transformer. 
 - pulsing the 110V or 220V power on/off will turn the light on/off
 - connected to a port on RelayModule to perform pulsing of power to turn the light on/off or change colors.

### Temperate Sensors
 - connected to the RPI 1-wire bus
 - multiple sensors can be connected to the bus in parallel
 - the RPI will read the temperature values from the sensors



