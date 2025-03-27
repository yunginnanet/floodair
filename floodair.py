#!/usr/bin/env python3

import argparse
import time
from random import randint, uniform

import numpy as np
import yaml
from gnuradio import gr, blocks, analog, digital

import ranger

try:
    from prettyprinter import cpprint
except:
    from pprint import pprint
import osmosdr  # noinspection PyUnresolvedReferences


# -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-


class FloodAir:
    def __init__(self, options):
        super(FloodAir, self).__init__()
        self.options = options

        self.signal_type = options.get("signal_type")
        self.signal_power = options.get("signal_power")

        self.hopper_entropy = False
        self.hopper_delay_static = options.get("hopper_delay_static")
        self.hopper_delay_min = options.get("hopper_delay_min")
        self.hopper_delay_max = options.get("hopper_delay_max")

        self.RF_gain = None
        self.IF_gain = None
        self.sink = None
        self.tb = None
        self.source = None
        self.sample_rate = 20e6
        self.bandwidth = 20e6
        self.setup_once = False

    def set_gains(self):
        if -40 <= self.signal_power <= 5:
            self.RF_gain = 0
            if self.signal_power < -5:
                self.IF_gain = self.signal_power + 40
            elif -5 <= self.signal_power <= 2:
                self.IF_gain = self.signal_power + 41
            elif 2 < self.signal_power <= 5:
                self.IF_gain = self.signal_power + 42
        elif self.signal_power > 5:
            self.RF_gain = 14
            self.IF_gain = self.signal_power + 34
        return self.RF_gain, self.IF_gain

    # noinspection TryExceptPass
    def set_freq(self, freq):
        try:
            self.sink.set_center_freq(freq, 0)
        except:
            pass

    def get_freq(self):
        try:
            f = self.sink.get_center_freq()
        except:
            f = self.options.get("frequency_start") * 10e5
        return f

    def print_freq(self):
        print(f"Let it eat: {self.get_freq() / 10e5}MHz\r")

    def _hop_wait(self):
        _wait = self.hopper_delay_static
        if self.hopper_entropy:
            _wait = uniform(self.hopper_delay_min, self.hopper_delay_max)
            return

        print(_wait, flush=True, end="")
        print("s...", flush=True, end="")
        time.sleep(_wait)

    def _waveform(self):
        if self.source:
            return

        throttle = blocks.throttle(gr.sizeof_gr_complex * 1, self.sample_rate, True)

        match self.signal_type:
            case 1:
                print("signal_type:\tsine")
                self.source = analog.sig_source_c(
                    self.sample_rate, analog.GR_SIN_WAVE, 1000, 1, 0, 0
                )
                self.tb.connect(self.source, throttle)
                self.tb.connect(throttle, self.sink)
            case 2:
                self.sink.set_sample_rate(self.sample_rate)

                print("signal_type:\tQPSK")
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
                print("signal_type:\tnoise")
                self.source = analog.noise_source_c(
                    analog.GR_GAUSSIAN, 1.0, randint(11111, 55555)
                )
                self.tb.connect(self.source, throttle)
                self.tb.connect(throttle, self.sink)

    def _sink(self, freq):
        try:
            soapy_string = self.options.get("device_soapy_str")
        except:
            soapy_string = "hackrf=0,bias_tx=0,if_gain=47,multiply_const=6"

        print(f"soapy:\t{soapy_string}")

        if not self.sink:
            try:
                self.sink = osmosdr.sink(args=soapy_string)
            except Exception as e:
                print(e)
                exit(1)

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
            self._waveform()
            return

        self.setup_once = True
        self.RF_gain, self.IF_gain = self.set_gains()

        self.tb = gr.top_block()
        self._sink(freq)
        self._waveform()

    def flood_run(self):
        self.tb.start()
        if self.options.get("hopper_mode") == 1:
            input("enter to stop\n\n")
        else:
            self._hop_wait()
        try:
            self.tb.stop()
        except Exception as e:
            raise e
        finally:
            self.tb.wait()

    def flood(self, freq):
        try:
            self.flood_setup(freq)
        except Exception as e:
            print(e)
            return e

        self.print_freq()
        try:
            self.flood_run()
        except Exception as e:
            print(e)
            return e

    def set_frequency(self, init_freq, channel):
        if channel == 1:
            freq = init_freq
        else:
            freq = init_freq + (channel - 1) * (
                self.options.get("frequency_delta") * 10e5
            )

        return freq

    def constant(self):
        try:
            self.flood(self.options.get("frequency_start"))
        except Exception as e:
            print(e)
            exit(1)

    def sweeping(self, init_freq, lst_freq):
        channel = 1
        n_channels = (lst_freq - init_freq) // (
            self.options.get("frequency_delta") * 10e5
        )

        while True:
            if channel > n_channels:
                channel = 1
            freq = self.set_frequency(init_freq, channel)

            try:
                self.flood(freq)
                channel += 1
            except Exception as e:
                print(e)
                self.setup_once = False
                time.sleep(0.001)

    def hopper(self, init_freq, lst_freq):
        freq_range = (round(lst_freq) - round(init_freq)) // (
            self.options.get("frequency_delta") * 10e5
        )
        channel = 1

        while True:
            freq = self.set_frequency(init_freq, channel)
            try:
                self.flood(freq)
            except Exception as e:
                print(e)
                self.setup_once = False
                time.sleep(0.001)

            channel = int(randint(1, round(freq_range + 1)))

    def rangin(self, iterable):
        started = False
        while True:
            for freq in iterable:
                freq = freq * 10e5
                try:
                    if started:
                        self.tb.stop()
                        self.tb.wait()

                    self.flood_setup(freq)
                    self.print_freq()
                    self.tb.start()
                    started = True
                except Exception as e:
                    print(e)
                    self.setup_once = False

            self.tb.stop()
            self.tb.wait()
            started = False


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


# noinspection TryExceptPass
def prompt_freqs(options):
    while True:
        _f = input("enter minimum center frequency in MHz: ")
        try:
            options["frequency_start"] = float(_f)
            break
        except:
            pass

    while True:
        _f = input("enter end center frequency in MHz: ")
        try:
            options["frequency_end"] = float(_f)
            break
        except:
            pass

    try:
        cpprint(options)
    except:
        pprint(options)

    print("\nusing default values", end="", flush=True)
    for i in range(1, 4):
        time.sleep(1)
        end = ""
        if i == 4:
            end = "\n\n"
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
        "--device_soapy_str",
        help="soapysdr device string",
        type=str,
        default=def_opts.get("device_soapy_str"),
    )
    ap.add_argument(
        "-f",
        "--frequency_start",
        help="min center frequency in MHz",
        type=float,
        default=def_opts.get("frequency_start"),
    )
    ap.add_argument(
        "-m",
        "--frequency-end",
        help="max center frequency in MHz",
        type=float,
        default=def_opts.get("frequency_end"),
    )
    ap.add_argument(
        "-p",
        "--signal_power",
        help="RF signal_power in dB",
        type=int,
        default=def_opts.get("signal_power"),
    )
    ap.add_argument(
        "-w",
        "--signal_type",
        help="source signal_type",
        type=int,
        default=def_opts.get("signal_type"),
        choices=[1, 2, 3],
    )
    ap.add_argument(
        "-o",
        "--hopper_mode",
        help="channel hopping mechanism",
        type=float,
        default=def_opts.get("hopper_mode"),
        choices=[1, 2, 3, 3.1, 4, 4.1],
    )
    ap.add_argument(
        "-t",
        "--hopper_delay_static",
        help="time to stay on each frequency hopped to",
        type=float,
        default=def_opts.get("hopper_delay_static"),
    )
    ap.add_argument(
        "-l",
        "--hopper_delay_min",
        help="minimum ([l]ower) value for random hopper_delay_static values",
        type=float,
        default=def_opts.get("hopper_delay_min"),
    )
    ap.add_argument(
        "-u",
        "--hopper_delay_max",
        help="maximum ([u]pper) value for random hopper_delay_static values",
        type=float,
        default=def_opts.get("hopper_delay_max"),
    )
    ap.add_argument(
        "-r",
        "--ranger_str",
        help="comma separated range values for ranger function, see config for more help",
        type=str,
        default=def_opts.get("ranger_str"),
    )
    return ap.parse_args()


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
        options = yaml.safe_load(config_file)
        config_file.close()

    except Exception as e:
        print(f"failed to load config ({args.config})\n{e}\n")
        options = def_opts
        options = prompt_freqs(options)

    options = merge_options(options, vars(args))

    try:
        cpprint(options)
    except:
        pprint(options)

    return options


def main():
    options = load_config()

    wavy = FloodAir(options)

    freq = options.get("frequency_start") * 10e5
    freq_max = options.get("frequency_end") * 10e5

    if freq_max < freq:
        print("frequency_end must be greater than frequency_start")
        exit(1)

    options["frequency_start"] = freq

    hopper_mechanism = options.get("hopper_mode")

    match hopper_mechanism:
        case 1:
            wavy.hopper_entropy = False
            wavy.constant()
        case 2:
            wavy.hopper_entropy = False
            wavy.sweeping(freq, freq_max)
        case 3:
            wavy.hopper_entropy = False
            wavy.hopper(freq, freq_max)
        case 3.1:
            wavy.hopper_entropy = True
            wavy.hopper(freq, freq_max)
        case 4:
            wavy.rangin(
                ranger.Ranger(
                    options.get("ranger_str"),
                    sleep_secs=options.get("hopper_delay_static"),
                )
            )
        case 4.1:
            wavy.hopper_entropy = True
            wavy.rangin(
                ranger.Ranger(
                    options.get("ranger_str"),
                    sleep_secs=options.get("hopper_delay_static"),
                    entropy=True,
                )
            )
        case _:
            print(
                "unknown 'hopper_mode'. options:\n",
                "1\tconstant\n",
                "2\tsweeping\n",
                "3\thopper\n",
                "3.1\thopper with entropy\n",
            )
            exit(1)


if __name__ == "__main__":
    main()
