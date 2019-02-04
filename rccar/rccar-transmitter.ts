/** CONSTANTS */
let COMMAND_FORWARDS = "F"
let COMMAND_BACKWARDS = "B"
let COMMAND_LEFT = "L"
let COMMAND_RIGHT = "R"

let COMMAND_STOP = "-"
let COMPLETE_STOP = COMMAND_STOP + COMMAND_STOP

let SENSITIVITY = 200

let CONTROL_ON_BTN = Button.A

/** VARIABLES */
let currentCommand = COMPLETE_STOP
let controllerOn = false

radio.setGroup(1)

/** When button pressed toggle the controller on and off */
input.onButtonPressed(CONTROL_ON_BTN, function () {
    controllerOn = !controllerOn
})

basic.forever(function () {
    if (controllerOn) {
        basic.showIcon(IconNames.Happy)
        sendCommand()
    } else {
        basic.showIcon(IconNames.Angry)
        sendStop()
    }
})

function sendStop() {
    radio.sendString(COMPLETE_STOP)
}

function sendCommand() {
    currentCommand = ""
    if (input.acceleration(Dimension.Y) < -SENSITIVITY) {
        currentCommand = COMMAND_FORWARDS
    } else if (input.acceleration(Dimension.Y) > SENSITIVITY) {
        currentCommand = COMMAND_BACKWARDS
    } else {
        currentCommand = COMMAND_STOP
    }

    if (input.acceleration(Dimension.X) < -SENSITIVITY) {
        currentCommand += COMMAND_LEFT
    } else if (input.acceleration(Dimension.X) > SENSITIVITY) {
        currentCommand += COMMAND_RIGHT
    } else {
        currentCommand += COMMAND_STOP
    }
    radio.sendString(currentCommand)
}
