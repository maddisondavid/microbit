
/** CONSTANTS */
let LEFT_GPIO = DigitalPin.P5
let RIGHT_GPIO = DigitalPin.P8
let FORWARD_GPIO = DigitalPin.P11
let BACKWARD_GPIO = DigitalPin.P13

let COMPLETE_STOP = "--"

let COMMAND_FORWARDS = "F"
let COMMAND_BACKWARDS = "B"
let COMMAND_LEFT = "L"
let COMMAND_RIGHT = "R"

// Indicates if the car should be processing any instructions
let running = false

let CurrentCommand = COMPLETE_STOP
let NewCommand = COMPLETE_STOP

radio.setGroup(1)

/**
  When we get a new direction from the controller store it so that it's processed
  by the next main loop
*/
radio.onReceivedString(function (command) {
    NewCommand = command
})

/**
   Loops forever repeating the last instruction we had until it changes
 */
basic.forever(function () {
    if (NewCommand != "") {
        CurrentCommand = NewCommand
        NewCommand = ""
    }

    processCommands()
})

/**
 * Process the instruction, turning pins off and on as required
 */
function processCommands() {
    if (CurrentCommand.charAt(0) == COMMAND_FORWARDS) {
        pins.digitalWritePin(FORWARD_GPIO, 1)
        led.plot(2, 4)
    } else {
        pins.digitalWritePin(FORWARD_GPIO, 0)
        led.unplot(2, 4)
    }

    if (CurrentCommand.charAt(0) == COMMAND_BACKWARDS) {
        pins.digitalWritePin(BACKWARD_GPIO, 1)
        led.plot(2, 0)
    } else {
        pins.digitalWritePin(BACKWARD_GPIO, 0)
        led.unplot(2, 0)
    }

    if (CurrentCommand.charAt(1) == COMMAND_LEFT) {
        pins.digitalWritePin(LEFT_GPIO, 1)
        led.plot(4, 2)
    } else {
        pins.digitalWritePin(LEFT_GPIO, 0)
        led.unplot(4, 2)
    }

    if (CurrentCommand.charAt(1) == COMMAND_RIGHT) {
        pins.digitalWritePin(RIGHT_GPIO, 1)
        led.plot(0, 2)
    } else {
        pins.digitalWritePin(RIGHT_GPIO, 0)
        led.unplot(0, 2)
    }
}

