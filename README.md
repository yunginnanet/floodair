# FloodAir

Currently only supporting `hackrf` devices, but technically with some fiddling of `device_soapy_str` you should be able to use almost any SDR supported by SoapySDR.

Using this is probably illegal. ~~Don't get caught!~~ ~~Don't use this?~~ ~~Fuck it!~~ Check your local laws, author is not responsible for damage caused when using this tool inappropriately.

## Usage

Ultimately, parameters are merged with the greater configuration sources taking priority and overriding the lesser;

#### CLI arguments (flags) > configuration values > default options

### default options

```python
def_opts = {
    "device_soapy_str": "hackrf=0,bias_tx=0,if_gain=47,multiply_const=6",

    "signal_power": 47,
    "signal_type": 3,

    "frequency_delta": 1,
    "frequency_min": 2400,
    "frequency_max": 2500,

    "hopper_mode": 3,
    "hopper_delay_static": 0.01,
    "hopper_delay_min": 0.001,
    "hopper_delay_max": 20,
}
```

### CLI

```
usage: floodair.py [-h] [-c CONFIG] [-d DEVICE_SOAPY_STR] [-f FREQUENCY_START]
                   [-m FREQUENCY_END] [-p SIGNAL_POWER] [-w {1,2,3}]
                   [-o {1,2,3,3.1}] [-t HOPPER_DELAY_STATIC]
                   [-l HOPPER_DELAY_MIN] [-u HOPPER_DELAY_MAX]

Flood the airwaves with RF noise

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file to load options from
  -d DEVICE_SOAPY_STR, --device_soapy_str DEVICE_SOAPY_STR
                        soapysdr device string
  -f FREQUENCY_START, --frequency_start FREQUENCY_START
                        min center frequency in MHz
  -m FREQUENCY_END, --frequency-end FREQUENCY_END
                        max center frequency in MHz
  -p SIGNAL_POWER, --signal_power SIGNAL_POWER
                        RF signal_power in dB
  -w {1,2,3}, --signal_type {1,2,3}
                        source signal_type
  -o {1,2,3,3.1}, --hopper_mode {1,2,3,3.1}
                        channel hopping mechanism
  -t HOPPER_DELAY_STATIC, --hopper_delay_static HOPPER_DELAY_STATIC
                        time to stay on each frequency hopped to
  -l HOPPER_DELAY_MIN, --hopper_delay_min HOPPER_DELAY_MIN
                        minimum ([l]ower) value for random hopper_delay_static
                        values
  -u HOPPER_DELAY_MAX, --hopper_delay_max HOPPER_DELAY_MAX
                        maximum ([u]pper) value for random hopper_delay_static
                        values
```


### Config

#### `config.yaml`

```yaml
---

  ######################
  #####   Device   #####
  ######################

device_soapy_str: "hackrf=0,bias_tx=1,if_gain=47,multiply_const=6,buffers=64"


  ######################
  #####   Signal   #####
  ######################

  # 1 = single tone
  # 2 = QPSK (Quadra Phase Key Shift Keying) modulated signal_type
  # 3 = gaussian noise (*)
signal_type: 2

# Note: consider removing this parameter
# in favor of parameters within device_soapy_str.
signal_power: 47


  ######################
  #####   Hopper   #####
  ######################

 # 1 = constant frequency
 # 2 = frequency sweeping
 # 3 = random frequency hopping
   # 3.1 = random frequency hopping with entropy
hopper_mode: 2

# (seconds) time to wait before hopping to the next frequency
hopper_delay_static: 5

hopper_delay_min: 1
hopper_delay_max: 10


  #####################
  ##### Frequency #####
  #####################

frequency_delta: 5
frequency_start: 905
frequency_end: 930

```

## Credit

Some snippets (particularly the QPSK modulation), [are from this repo](https://github.com/tiiuae/jamrf/tree/master/HackRF).
