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
    "frequency_start": 2400,
    "frequency_end": 2500,

    "hopper_mode": 3,
    "hopper_delay_static": 0.01,
    "hopper_delay_min": 0.001,
    "hopper_delay_max": 20,

    "ranger_str": "1600,2300,r:2400-2500_1",
}
```

### CLI

```
usage: floodair.py [-h] [-c CONFIG] [-d DEVICE_SOAPY_STR] [-f FREQUENCY_START]
                   [-m FREQUENCY_END] [-p SIGNAL_POWER] [-w {1,2,3}]
                   [-o {1,2,3,3.1,4,4.1}] [-t HOPPER_DELAY_STATIC]
                   [-l HOPPER_DELAY_MIN] [-u HOPPER_DELAY_MAX] [-r RANGER_STR]

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
  -o {1,2,3,3.1,4,4.1}, --hopper_mode {1,2,3,3.1,4,4.1}
                        channel hopping mechanism
  -t HOPPER_DELAY_STATIC, --hopper_delay_static HOPPER_DELAY_STATIC
                        time to stay on each frequency hopped to
  -l HOPPER_DELAY_MIN, --hopper_delay_min HOPPER_DELAY_MIN
                        minimum ([l]ower) value for random hopper_delay_static
                        values
  -u HOPPER_DELAY_MAX, --hopper_delay_max HOPPER_DELAY_MAX
                        maximum ([u]pper) value for random hopper_delay_static
                        values
  -r RANGER_STR, --ranger_str RANGER_STR
                        comma separated range values for ranger function, see
                        config for more help
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
signal_type: 3

# Note: consider removing this parameter
# in favor of parameters within device_soapy_str.
signal_power: 47


  ######################
  #####   Hopper   #####
  ######################

 # - 1        constant frequency
 # - 2        frequency sweeping
 # - 3        random frequency hopping
 #   - 3.1            \--> (with entropic delay)
 # - 4        ranger function string (see below)
 #   - 4.1            \--> (with entropic delay)
hopper_mode: 3.1

# (seconds) time to wait before hopping to the next frequency
hopper_delay_static: 20

hopper_delay_min: 0.01
hopper_delay_max: 0.1

# comma separated items;
#    - freq:                            single frequency (%f)
#    - freqmin-freqmax:                 frequency range (%f-%f)
#    - freqmin-freqmax_delta:           frequency range with step (%f-%f_%f)
#    - freqmin-freqmax_delta;delaysecs: frequency range with step and delay (%f-%f_%f;%f)
#    - r:freqmin-freqmax_delta:         random frequency range with step (%f-%f_%f)
#
# Examples:
#    - "2400"                             # 2400Mhz
#    - "2400-2500"                        # 2400-2500Mhz sweep        
#    - "2400-2500_1"                      # 2400-2500Mhz sweep with 1Mhz step
#    - "r:2400-2500_1"                    # random frequency between 2400-2500Mhz with 1Mhz step
#    - "2400,r:2400-2500_1, 2500"         # 2400Mhz, random frequency between 2400-2500Mhz with 1Mhz step, then 2500Mhz
#    - "2400-2500_1;0.1, 2500-2600_1;0.2" # 2400-2500Mhz sweep with 1Mhz step and 0.1s delay, then 2500-2600Mhz sweep with 1Mhz step and 0.2s delay

ranger_str: "r:3850-4075_1;0.1,910-925_1;0.2,r:1300-1700_1;0.2,2350;5"

  #####################
  ##### Frequency #####
  #####################

frequency_delta: 0.1
frequency_start: 910
frequency_end: 925
```

## Credit

Some snippets (particularly the QPSK modulation), [are from this repo](https://github.com/tiiuae/jamrf/tree/master/HackRF).
