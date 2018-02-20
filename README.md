# piface-digital-web-api

A simple web interface to control your [PiFace Digital](http://www.piface.org.uk/products/piface_digital/) inputs and outputs written in Python using [Flask](https://github.com/pallets/flask).

## Setup
```
git clone https://github.com/robsonvn/piface-digital-web-api.git
cd piface-digital-web-api
cp .env.example .env
```
You can read more about Environment Variables [here](#environment-variables).
## Running

FLASK_APP=app.py flask run --host 0.0.0.0 --port 8080

## Endpoints

### Device state (/)

```
  curl -X GET http://127.0.0.1:8080/
```
#### Result
```json
{
  "device_id": "10.0.0.77",
  "flick_sleep_interval": 1,
  "number_of_inputs": 8,
  "number_of_outputs": 8,
  "states": {
    "inputs": [
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0
    ],
    "outputs": [
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0
    ]
  },
  "uptime": "0:00:34.838569"
}
```

### Flick output (/output/{output_number}/flick)
```
  curl -X GET http://127.0.0.1:8080/output/0/flick
```

Response: the current device state

*The default delay time is 1 second, but you can define a custom value in your .env file using* FLICK_SLEEP_INTERVAL

### Turn output on (/output/{output_number}/on)
```
  curl -X GET http://127.0.0.1:8080/output/0/on
```

Response: the current device state

### Turn output off (/output/{output_number}/off)
```
  curl -X GET http://127.0.0.1:8080/output/0/off
```

Response: the current device state

## Webhook

You can use Webhook to notify your application whenever an input state changes by adding INPUT_WEBHOOK in your .env file.


Example:
```
INPUT_WEBHOOK=http://10.0.0.200:3030/webhooker/raspberry/
```

A GET request will be performed with the following parameters:

* **device_id** the device id set in your .env file
* **input** the input number
* **event** the input event (on/off)

Example:
When the input number 2 goes on, the following request will be performed:
```
curl -X GET http://10.0.0.200:3030//webhooker/raspberry/?device_id=10.0.0.77&input=2&event=on
```

**Note:** The request will be performed only once, regardless the response code.

## Environment Variables

* **DEVICE_ID** the device unique identifier (mandatory)
* **FLICK_SLEEP_INTERVAL** the sleep interval in seconds when flicking an output (default: 1)
* **NUMBER_OF_INPUTS** the number of inputs to be controlled (default: 8)
* **NUMBER_OF_OUTPUTS** the number of outputs to be controlled (default: 8)
* **INPUT_WEBHOOK** the URL to be requested when an input state changes

## Limitations

* There is no API guard.

## TODO

* Implement API guard.
