import asyncio
import aiohttp
import logging
import logging.config
import pifacedigitalio
import requests
import yaml

from aiohttp import web
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from multiprocessing import Process
from os import environ
from os.path import join, dirname, isfile
from time import sleep

if isfile('logging.conf'):
    logging.config.dictConfig(yaml.load(open('logging.conf')))

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

FLICK_SLEEP_INTERVAL = environ.get("FLICK_SLEEP_INTERVAL") or 1
NUMBER_OF_INPUTS = int(environ.get("NUMBER_OF_INPUTS") or 8)
NUMBER_OF_OUTPUTS = int(environ.get("NUMBER_OF_OUTPUTS") or 8)
WEBHOOK_URL = environ.get("WEBHOOK_URL")
DEVICE_ID = environ.get("DEVICE_ID")
DEBUG = environ.get("DEBUG") or False
startTime = datetime.now()

'''
    Routes
'''

def init_func(argv):
    app = web.Application(debug=DEBUG)
    app.router.add_get('/', index)
    app.router.add_get('/output/flick', flick_output_handler)
    app.router.add_get('/output/on', turn_relay_on)
    app.router.add_get('/output/off', turn_relay_off)
    return app

async def index(request):
    return web.json_response(get_device_states())

def flick_output_handler(request):
    p = Process(target=flick_output_relay, args=(request,))
    p.start()
    return web.json_response(get_device_states())

def flick_output_relay(request):
    turn_relay_on(request)
    interval = float(request.rel_url.query.get('interval', FLICK_SLEEP_INTERVAL))
    sleep(interval)
    turn_relay_off(request)


def turn_relay_on(request):
    outputs = get_output_numbers(request)
    for output in outputs:
        if validate_output_number(output):
            pifacedigital.output_pins[output].turn_on()
            notify_output_change(output, 'on')
    return web.json_response(get_device_states())

def turn_relay_off(request):
    outputs = get_output_numbers(request)
    for output in outputs:
        if validate_output_number(output):
            pifacedigital.output_pins[output].turn_off()
            notify_output_change(output, 'off')
    return web.json_response(get_device_states())


def get_output_numbers(request):
    outputs = request.rel_url.query.getall('output', [])
    return list(map(int, outputs))

def get_device_states():
    return {
        'device_id': DEVICE_ID,
        'states': {
            'inputs': get_inputs_state(),
            'outputs': get_outputs_state()
        },
        'number_of_inputs': NUMBER_OF_INPUTS,
        'number_of_outputs': NUMBER_OF_OUTPUTS,
        'flick_sleep_interval': FLICK_SLEEP_INTERVAL,
        'uptime': (datetime.now() - startTime).total_seconds()
    }

def validate_output_number(output):
    return output in range(NUMBER_OF_OUTPUTS)


def get_input_state(input):
    return pifacedigital.input_pins[input].value


def get_output_state(output):
    return pifacedigital.output_pins[output].value


def get_inputs_state():
    return list(map(get_input_state, range(NUMBER_OF_INPUTS)))


def get_outputs_state():
    return list(map(get_output_state, range(NUMBER_OF_OUTPUTS)))


def on_press_handler(event):
    notify_input_change(event.pin_num, 'on')


def on_release_handler(event):
    notify_input_change(event.pin_num, 'off')


def notify_output_change(output_number, value):
    logging.info("Output {0} is now {1}".format(output_number,value))
    #threading request
    p = Process(target=notify_web_hooker, args=('output', output_number, value,))
    p.start()

def notify_input_change(input_number, value):
    logging.info("Input {0} is now {1}".format(input_number,value))
    #threading request
    p = Process(target=notify_web_hooker, args=('input', input_number, value,))
    p.start()

def notify_web_hooker(event_type, event_number, event_value):
    if WEBHOOK_URL:
        requests.get(WEBHOOK_URL, params={'device_id': DEVICE_ID, 'event_type': event_type, 'event_number': event_number, 'event_value': event_value})

'''
    Input listeners
'''

pifacedigital = pifacedigitalio.PiFaceDigital()
listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
for i in range(NUMBER_OF_INPUTS):
    listener.register(i, pifacedigitalio.IODIR_ON, on_press_handler)
    listener.register(i, pifacedigitalio.IODIR_OFF, on_release_handler)
listener.activate()
