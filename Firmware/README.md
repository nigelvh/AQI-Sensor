# AQI Sensor Firmware
This firmware is specific to the device described in the hardware section. It is a chunk of code for use with [MicroPython](https://micropython.org/) on the ESP32. I have used the `esp32-20220618-v1.19.1.bin` MicroPython release in my deployments. I don't believe there's anything extraordinary in the code, but I can't guarantee other releases won't change something.

I make use of the [Microdot library](https://microdot.readthedocs.io/en/latest/index.html) to handle the web server portion of the application. For memory considerations, I pre-compiled the `microdot` and `microdot_asyncio` into their respective `.mpy` files.

All of the remaining libraries are shipped default with MicroPython or I have written and included myself.

## Tweaks
In `boot.py` you will need to fill in your own data for the `POST_URL` and `UPDATE_URL` fields. The `POST_URL` field is simply the URL the device will send a POST request to once per minute, with JSON encoded data in the POST body. Parsing/storing/displaying that data is left as an exercise to the user. The `UPDATE_URL` field is the URL *to a folder* where the device will expect to find a `version.json` file which will enumerate the files to be downloaded and their SHA1 sums for verification. I'm not going to document this further because it's probably garbage, but the update.py code shouldn't be terribly obtuse if you really want to use it.

## Disclaimer
I'm not a coder by trade. I don't make any guarantees about the quality of the code. In fact it's probably pretty bad. It works for me on my devices. If you have improvements, feel free to send them along.
