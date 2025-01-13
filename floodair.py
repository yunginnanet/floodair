#!/usr/bin/env python3

import argparse
import time
from random import randint
import yaml

from gnuradio import gr, blocks, analog, digital
import numpy as np

try:
    from prettyprinter import cpprint
except:
    from pprint import pprint


# -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

class FloodAir:
    def __init__(self, options):
        super(FloodAir, self).__init__()
        self.options = options
        self.waveform = options.get("waveform")
        self.power = options.get("power")
        self.hop_time = options.get("hop_time")
        self.RF_gain = None
        self.IF_gain = None
        self.sink = None
        self.tb = None
        self.source = None
        self.sample_rate = 20e6
        self.bandwidth = 20e6
        self.setup_once = False

    def set_gains(self):
        if -40 <= self.power <= 5:
            self.RF_gain = 0
            if self.power < -5:
                self.IF_gain = self.power + 40
            elif -5 <= self.power <= 2:
                self.IF_gain = self.power + 41
            elif 2 < self.power <= 5:
                self.IF_gain = self.power + 42
        elif self.power > 5:
            self.RF_gain = 14
            self.IF_gain = self.power + 34
        return self.RF_gain, self.IF_gain

    def set_freq(self, freq):
        try:
            self.sink.set_center_freq(freq, 0)
        except:
            pass

    def get_freq(self):
        try:
            f = self.sink.get_center_freq()
        except:
            f = self.options.get("freq_center") * 10e5
        return f

    def print_freq(self):
        print(f"\nLet it eat: {self.get_freq() / 10e5}MHz")

    def _waveform(self):
        throttle = blocks.throttle(gr.sizeof_gr_complex * 1, self.sample_rate, True)

        match self.waveform:
            case 1:
                print("waveform:\tsine")
                self.source = analog.sig_source_c(
                    self.sample_rate, analog.GR_SIN_WAVE, 1000, 1, 0, 0
                )
                self.tb.connect(self.source, throttle)
                self.tb.connect(throttle, self.sink)
            case 2:
                print("waveform:\tQPSK")
                qpsk = digital.generic_mod(
                    constellation=digital.constellation_rect(
                        [-1 - 1j, -1 + 1j, 1 + 1j, 1 - 1j], [0, 1, 3, 2], 4, 2, 2, 1, 1
                    ).base(),
                    differential=True,
                    samples_per_symbol=4,
                    pre_diff_code=True,
                    excess_bw=0.035,
                    verbose=True,
                )
                self.source = blocks.vector_source_b(
                    list(map(int, np.random.randint(0, 255, 1000))), True
                )
                self.tb.connect(self.source, qpsk)
                self.tb.connect(qpsk, throttle, self.sink)

            case 3:
                print("waveform:\tnoise")
                self.source = analog.noise_source_c(
                    analog.GR_GAUSSIAN, 1.0, randint(11111, 55555)
                )
                self.tb.connect(self.source, throttle)
                self.tb.connect(throttle, self.sink)

    def _sink(self, freq):
        try:
            soapy_string = self.options.get("soapy_sdr")
            if soapy_string is None:
                raise Exception
        except:
            soapy_string = "hackrf=0,bias_tx=0,if_gain=47,multiply_const=6"

        print(f"soapy:\t{soapy_string}")

        try:
            import osmosdr # noinspection PyUnresolvedReferences
        except ImportError:
            print("Error: osmosdr module not found")
            exit(1)

        self.sink = osmosdr.sink(args=soapy_string)

        self.sink.set_time_unknown_pps(osmosdr.time_spec_t())
        self.sink.set_sample_rate(self.sample_rate)
        self.sink.set_center_freq(freq, 0)
        self.sink.set_freq_corr(0, 0)
        self.sink.set_gain(self.RF_gain, 0)
        self.sink.set_if_gain(self.IF_gain, 0)
        self.sink.set_bb_gain(20, 0)
        self.sink.set_antenna("", 0)
        self.sink.set_bandwidth(self.bandwidth, 0)

    def flood_setup(self, freq):
        self.set_freq(freq)

        if self.setup_once is True:
            return

        self.setup_once = True
        self.RF_gain, self.IF_gain = self.set_gains()

        self.tb = gr.top_block()
        self._sink(freq)
        self._waveform()

    def flood_run(self):
        self.tb.start()
        time.sleep(self.hop_time)
        self.tb.stop()
        self.tb.wait()

    def flood(self, freq):
        self.flood_setup(freq)
        self.print_freq()
        self.flood_run()

    def set_frequency(self, init_freq, channel):
        if channel == 1:
            freq = init_freq
        else:
            freq = init_freq + (channel - 1) * (self.options.get("freq_delta") * 10e5)

        return freq

    def constant(self):
        freq = self.options.get("freq_center") * 10e5
        self.flood(freq)
        time.sleep(self.options.get("hop_time"))

    def sweeping(self, init_freq, lst_freq):
        channel = 1
        n_channels = (lst_freq - init_freq) // (self.options.get("freq_delta") * 10e5)

        while True:
            if channel > n_channels:
                channel = 1
            freq = self.set_frequency(init_freq, channel)
            time.sleep(self.options.get("hop_time"))
            self.flood(freq)
            channel += 1

    def hopping(self, init_freq, lst_freq):
        freq_range = (round(lst_freq) - round(init_freq)) // (
                self.options.get("freq_delta") * 10e5
        )
        channel = 1

        while True:
            freq = self.set_frequency(init_freq, channel)
            time.sleep(self.options.get("hop_time"))
            self.flood(freq)
            channel = int(randint(1, round(freq_range + 1)))


def_opts = {
    "soapy_sdr": "hackrf=0,bias_tx=0,if_gain=47,multiply_const=6",
    "freq_delta": 1,
    "power": 47,
    "hop_time": 0.01,
    "waveform": 3,
    "hopper": 3,
}


def prompt_freqs(options):
    while True:
        _f = input("enter minimum center frequency in MHz: ")
        try:
            options["freq_center"] = float(_f)
            break
        except:
            continue

    while True:
        _f = input("enter end center frequency in MHz: ")
        try:
            options["freq_max"] = float(_f)
            break
        except:
            continue

    try:
        cpprint(options)
    except:
        pprint(options)

    print("\nusing default values", end='', flush=True)
    for i in range(1, 4):
        time.sleep(1)
        end = ''
        if i == 4:
            end = '\n\n'
        print(".", end=end, flush=True)

    return options


def arg_parser():
    ap = argparse.ArgumentParser(description="Flood the airwaves with RF noise")
    ap.add_argument(
        "-c",
        "--config",
        help="config file to load options from",
        default="config.yaml",
    )
    ap.add_argument(
        "-d",
        "--soapy_sdr",
        help="soapysdr device string",
        type=str,
        default=def_opts.get("soapy_sdr"),
    )
    ap.add_argument(
        "-f",
        "--freq_min",
        help="min center frequency in MHz",
        type=float,
        default=def_opts.get("freq_center"),
    )
    ap.add_argument(
        "-m",
        "--freq-max",
        help="max center frequency in MHz",
        type=float,
        default=def_opts.get("freq_max"),
    )
    ap.add_argument(
        "-p",
        "--power",
        help="RF power in dB",
        type=int,
        default=def_opts.get("power"),
    )
    ap.add_argument(
        "-t",
        "--hop_time",
        help="time to stay on each frequency hopped to",
        type=float,
        default=def_opts.get("hop_time"),
    )
    ap.add_argument(
        "-w",
        "--waveform",
        help="source waveform",
        type=int,
        default=def_opts.get("waveform"),
    )
    ap.add_argument(
        "-o",
        "--hopper",
        help="channel hopping mechanism",
        type=int,
        default=def_opts.get("hopper"),
    )
    return ap.parse_args()

# write function to merge config file and command line args, prioritizing command line args
def merge_options(options, arg_vars):
    for key, value in arg_vars.items():
        if key == "config":
            continue
        if value is not None and value != def_opts[key]:
            options[key] = value
    return options

def load_config():
    args = arg_parser()

    try:
        config_file = open(args.config, "r")
        options = yaml.load(config_file, Loader=yaml.FullLoader)
        config_file.close()

    except Exception as e:
        print(f"failed to load config ({args.config})\n{e}\n")
        options = def_opts
        options = prompt_freqs(def_opts)

    options = merge_options(options, vars(args))

    try:
        cpprint(options)
    except:
        pprint(options)

    return options


def main():
    options = load_config()

    wavy = FloodAir(options)

    freq = options.get("freq_center") * 10e5
    freq_max = (options.get("freq_max") * 10e5)

    if freq_max < freq:
        print("freq_max must be greater than freq_center")
        exit(1)

    options["freq_center"] = freq

    hopper_mechanism = options.get("hopper")

    match hopper_mechanism:
        case 1:
            wavy.constant()
        case 2:
            wavy.sweeping(freq, freq_max)
        case 3:
            wavy.hopping(freq, freq_max)
        case _:
            print(
                "unknown hopper mechanism. options:\n",
                "1\tconstant\n",
                "2\tsweeping\n",
                "3\thopping",
            )
            exit(1)


if __name__ == "__main__":
    main()
