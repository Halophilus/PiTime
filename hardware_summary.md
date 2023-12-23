# PiTime HARDWARE README

## Introduction

![Project Overview](/docs/title.png)

This is the hardware section of the documentation for the PiTime project, Here, I will cover the technical challenges overcame to put this device together.

## Table of Contents
1. [Introduction](#introduction)
2. [Components](#components)
3. [Assembly Breakdown](#assembly-breakdown)
    - [Screen](#screen)
    - [Snooze Button](#snooze-button)
    - [Raspberry Pi Zero W](#raspberry-pi)
    - [Boost Converter](#boost-converter)
    - [Vibration Module](#vibration-module)
    - [Buzzer](#buzzer)
    - [Speaker](#speaker)
4. [Usage](#usage)
5. [Future Enhancements](#future-enhacements)
6. [Acknowledgements](#acknowledgements)
6. [License](#License)

---

## Components

| Component | Description | Notes | Quantity |
|-----------|-------------|-----------|-----------|
| Speaker | 8 Ohm 2W 28mm Loud Speakers | These fit the form factor for the project but are a little quiet. I'm going to see if using a different amp makes a difference, but it might be worth it to do more research. The ones I used come with and SMD mounting plug. | 1 |
| Microcontroller | Raspberry Pi Zero W | This project is best suited for SFF microcontrollers with built-in wireless functionality. | 1 |
| Button | Momentary tactile pushbutton | Any button will do, but make sure its suitable for the size of the case you're using | 1 |
| LCD Screen | I2C RG1206A 16x2 char Screen | A slightly larger display might allow for more information that can be displayed at once, but this size is all you need | 1 |
| 5V USB PSU | Type-C USB 5V 2A Boost Converter Step-Up Power Module Lithium Battery Charging Protection Board | Most of this project was powered through the USB passthrough on this boost converter, but for the final version of this product, there is the option of adding a battery | 1 |
| ULN 2803 | Darlington Transistor Array for PWM applications | Has a built-in freewheeling diode for motor kickback current and can have multiple pins bridged for higher current tolerance | 1 |
| Vibration Motor | 5V DC ERM Motor | 5V ERM motors are hard to come by, but I went with this one so I could get the maximum possible power out of it | 1 |
| Buzzer | Logic-level (3.3V) passive piezoelectric tone speaker | These are extremely loud at 3.3V, which might be what you're going for. If not, look into adding an in-line resistor to limit cut the volume. | 1 |
| Resistors | 270ohm, 150ohm, 8ohm, 15Kohm, 1Kohm | Needed to build the circuits used in this project. | 5 total, but you should buy a variety pack if you don't have one already |
| Capacitors | 100nf (ceramic), 10uF (electrolytic) | Necessary for hi-pass filter circuit | 2, can sometimes be harvested from common electronics |
| NPN Transistors | 2N2222 | Used for transistor amp | 1 |
| Wiring | Multi-colored 16awg solid-core multi-colored wire | Useful for holding components in place without worrying about moving/breaking | 2 feet each color |
| Jumpers | Multi-colored male-to-female jumper wires | Useful for connecting the RPi/PSU to the pins on the LCD-Screen | 4 pcs. |
| Protoboards | Hard prototyping perfboards for building dedicated circuits | Indispensable for a product like this, gives a permanent home to each component | 2 1x4" |


## Assembly Breakdown

This device was constructed piecemeal and each peripheral was added to the Raspberry Pi when complete. This section will cover basic composition of each peripheral, GPIO attachement, and expected behavior.

![Breakdown of different components](/docs/hardware/hardware.png)

1. [Screen](#screen)
2. [Snooze Button](#snooze-button)
3. [Raspberry Pi Zero W](#raspberry-pi)
4. [Boost Converter](#boost-converter)
5. [Vibration Module](#vibration-module)
6. [Buzzer](#buzzer)
7. [Speaker](#speaker)

### Screen

- The screen is a text-only LCD display controlled by I2C Protocol.
- Its SDA and SCL pins should be connected to the corresponding ouptut pins on the RPi.
- The power and ground should be attached to the 5V rails on the boost converter to reduce current sourcing on the RPi.

### Snooze Button

- A simple tactile button associated with the snoozing function.
- A 1Kohm resistor should be wired in-line with this button to avoid a short with a pin in the event that output was accidentally assigned to it. This will not affect button functionality.
- The button is attached to GPIO 23.
- Make sure the grounds between the RPi and the Boost Converter, as the circuits overlap in varying capacities.

### Boost Converter
- Main power source for the project.
- Primarily used for USB passthrough, but has the option to add a battery, which would be a necessary part of the final implementation of this project.
- No switch associated with it because the clock should never be turned off.
- While providing power through USB would be possible with this board, I chose to power the RPi by its 5V rails for the sake of compact storage.

### Vibration Module

![Vibration Circuit](/docs/hardware/circuits/vibration.png)

- This circuit utilizes a ULN2803 chip to control a 5V potential across an ERM vibration motor.
- Since only one speed is desired, instead of using PWM, the GPIO control is either high (on) or low (off).
- The motor is hooked up directly to the 5V rail on the power supply and the negative post is drained into the ULN2803.
- The signal is sent to the ULN2803 from GPIO 25.

### Buzzer

- A simple logic-level piezoelectric speaker.
- Can be powered directly by GPIO and draws little current.
- Self-oscillating so PWM is not necessary to generate tones.
- VERY loud at no limiting resistance (think fire alarm), so the addition of an in-line resistor or a potentiometer might be beneficial to anyone else who might be sleeping nearby.
- Possible other solutions include being able to set the volume digitally by having different GPIO pins with different in-line resistors. This could allow for an escalating alarm feature in the future. Diodes could be used to separate the GPIO pins and avoid a short.
- The Buzzer is connected to GPIO 17.

### Speaker

![Speaker Amplification/Filter Circuit](/docs/hardware/circuits/speaker.png)

- The Raspberry Pi Zero does not have on-board audio by default.
- Audio output can be assigned to one of the PWM GPIO pins (in this case, pin 18).
- This includes a high-pass filter and a basic 5V amp.
- This circuit produces very quiet audio, so I may replace it in the future for an alternative (e.g., an op amp such as the LM386)
- The quiet volume is bad for alarm sounds, but good for event details as the user has to focus in order to hear them, adding to the engagement with the device.

---

## Usage

Most instructions on how to utilize this program are included in the [README file](/README.md), but a basic recap is as follows:

- Start up the device.
- Write down the IP address as it appears on the LCD. This will be used to access the web interface.
- Go to the link `<ip address>:5000` in your browser to access the web app.
    - The main page is for submitting new events and reminders.
    - Reminders can be configured to set off different peripherals/features here.
    - Events and reminders can be reviewed and deleted on the Events page.
- Standard alarms can be shut off with the snooze button.
- Web-unlock alarms require the string on the LCD to be entered into the URL `<ip address>:5000/unlock/<unlock key>` to fully disengage the alarm.

## Future Enhancements

- Battery power.
- Low battery alerts
- Variable buzzer volumes.
- More robust amplifier.
- 3D-printed case.
- External pins for custom peripherals.

## Acknowledgements

Circuit diagrams were created using LTSpice(R) by Analog Devices.

## License
This project is licensed under the GNU General Public License v3.0 - see the [LICENSE file](LICENSE.txt) for details.
