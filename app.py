import pifacedigitalio
import logging, logging.config, yaml
from requests import Session, Request
from flask import Flask, jsonify, abort
from time import sleep
from os import environ
from os.path import join, dirname, isfile
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

if isfile('logging.conf'):
    logging.config.dictConfig(yaml.load(open('logging.conf')))

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

FLICK_SLEEP_INTERVAL = int(environ.get("FLICK_SLEEP_INTERVAL") or 1)
NUMBER_OF_INPUTS = int(environ.get("NUMBER_OF_INPUTS") or 8)
NUMBER_OF_OUTPUTS = int(environ.get("NUMBER_OF_OUTPUTS") or 8)
INPUT_WEBHOOK = environ.get("INPUT_WEBHOOK")
DEVICE_ID = environ.get("DEVICE_ID")
startTime = datetime.now()

app = Flask(__name__)

'''
    Routes
'''


@app.route('/')
def getDeviceState():
    return jsonify({
        'device_id': DEVICE_ID,
        'states': {
            'inputs': getInputsState(),
            'outputs': getOutputsState()
        },
        'number_of_inputs': NUMBER_OF_INPUTS,
        'number_of_outputs': NUMBER_OF_OUTPUTS,
        'flick_sleep_interval': FLICK_SLEEP_INTERVAL,
        'uptime': str(datetime.now() - startTime)
    })


@app.route('/output/<int:output>/flick')
def flickOutput(output):
    turnRelayOn(output)
    sleep(FLICK_SLEEP_INTERVAL)
    turnRelayOff(output)
    return getDeviceState()


@app.route('/output/<int:output>/on')
def turnRelayOn(output):
    validateRequest(output)
    pifacedigital.output_pins[output].turn_on()
    return getDeviceState()


@app.route('/output/<int:output>/off')
def turnRelayOff(output):
    validateRequest(output)
    pifacedigital.output_pins[output].turn_off()
    return getDeviceState()


def validateRequest(output):
    if not output in range(NUMBER_OF_OUTPUTS):
        abort(404)


def getInputState(input):
    return pifacedigital.input_pins[input].value


def getOutputState(output):
    return pifacedigital.output_pins[output].value


def getInputsState():
    return list(map(getInputState, range(NUMBER_OF_INPUTS)))


def getOutputsState():
    return list(map(getOutputState, range(NUMBER_OF_OUTPUTS)))


def onPressHandler(event):
    logging.info("Input {0} is now on".format(event.pin_num))
    if INPUT_WEBHOOK:
        notifyWebHooker(event.pin_num, 'on')


def onReleaseHandler(event):
    logging.info("Input {0} is now off".format(event.pin_num))
    if INPUT_WEBHOOK:
        notifyWebHooker(event.pin_num, 'off')


def notifyWebHooker(input_number, event):
    payload = {'device_id': DEVICE_ID, 'input': input_number, 'event': event}
    s = Session()
    req = Request('GET', INPUT_WEBHOOK, params=payload).prepare()
    try:
        res = s.send(req)
        logging.info("Webhook has been notified at: {0}\nResponse: ({1}): {2}".format(
            req.url, res.status_code, res.content))
    except IOError as err:
        logging.error("Webhook request failed {0}\nError:{1}".format(req.url, err))


'''
    Input listeners
'''

pifacedigital = pifacedigitalio.PiFaceDigital()
listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
for i in range(NUMBER_OF_INPUTS):
    listener.register(i, pifacedigitalio.IODIR_ON, onPressHandler)
    listener.register(i, pifacedigitalio.IODIR_OFF, onReleaseHandler)
listener.activate()
