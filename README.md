# FloodAir
### Flood the airwaves with RF noise

## CLI

`usage: floodair.py [-h] [-c CONFIG] [-d SOAPY_SDR] [-f FREQ_MIN] [-m FREQ_MAX] [-p POWER] [-t HOP_TIME] [-w WAVEFORM] [-o HOPPER]`

```
options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file to load options from
  -d SOAPY_SDR, --soapy_sdr SOAPY_SDR
                        soapysdr device string
  -f FREQ_MIN, --freq_min FREQ_MIN
                        min center frequency in MHz
  -m FREQ_MAX, --freq-max FREQ_MAX
                        max center frequency in MHz
  -p POWER, --power POWER
                        RF power in dB
  -t HOP_TIME, --hop_time HOP_TIME
                        time to stay on each frequency hopped to
  -w WAVEFORM, --waveform WAVEFORM
                        source waveform
  -o HOPPER, --hopper HOPPER
                        channel hopping mechanism
```

## Config

```yaml
---
soapy_sdr: "hackrf=0,bias_tx=0,if_gain=47,multiply_const=6"

 ## FloodAir Type
    # 1 = constant frequency
    # 2 = frequency sweeping
    # 3 = random frequency hopping
hopper: 3

 ## Waveform
    # 1 = single tone
    # 2 = QPSK (Quadra Phase Key Shift Keying) modulated waveform
    # 3 = gaussian noise (*)
waveform: 2

## Hop Time (s)
hop_time: 0.001

## Power
power: 47

freq_delta: 1
freq_min: 2000
freq_max: 3000
```
