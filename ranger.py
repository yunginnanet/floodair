from enum import Enum
from random import uniform, shuffle
import time


class RangeMode(Enum):
    ONE = 0
    STATIC = 1
    STOP = 2
    RANDOM = 3
    SEQUENCE = 4

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value


class Range:
    # noinspection PySameParameterValue
    def __init__(
        self,
        rstart=1.0,
        rend=None,
        delta=None,
        rmode=RangeMode.SEQUENCE,
        maxiter=None,
        sleep_secs=0.0,
    ):
        self.mode = rmode
        self._delay = sleep_secs
        self._start = float(rstart)

        if rend and rstart > rend:
            self._start, rend = rend, rstart

        try:
            self._delta = float(delta)
        except:
            if int(self._start) >= 0:
                self._delta = 1.0
            elif self._start < 1:
                self._delta = 0.1

        try:
            self._end = float(rend)
            self._index = float(rstart) - self._delta
        except Exception as e:
            if not ((self.mode == RangeMode.STATIC) or (self.mode == RangeMode.STOP)):
                raise e
            self._delta = 0.0
            self._end = self._start

        if self.mode == RangeMode.STOP:
            self._mode = RangeMode.STATIC
        else:
            self._mode = self.mode

        if not maxiter:
            match self.mode:
                case RangeMode.RANDOM:
                    self.maxiter = int((self._end - self._start) / self._delta) + 1
                case RangeMode.SEQUENCE:
                    self.maxiter = int((self._end - self._start) / self._delta) + 1
                case RangeMode.STATIC:
                    raise Exception("maxiter required for static mode")
                case RangeMode.ONE:
                    self.maxiter = 1
                case _:
                    self.maxiter = -1
        else:
            self.maxiter = int(maxiter)

        self._count = 0

    def __len__(self):
        if self.maxiter < 0:
            return int((self._end - self._start) / self._delta)
        return self.maxiter

    def __str__(self):
        return f"Range(_start={self._start}, _end={self._end}, _delta={self._delta}, mode={self.mode}, maxiter={self.maxiter}, _delay={self._delay})"

    def __iter__(self):
        return self

    def __next__(self):
        try:
            if self.mode == RangeMode.STOP:
                raise StopIteration
            if self.mode == RangeMode.ONE and self._count > 0:
                raise StopIteration
            if self.maxiter and (self.maxiter > 0) and (self._count >= self.maxiter):
                self._count = 0
                self.reset()
                raise StopIteration
            match self.mode:
                case RangeMode.STATIC:
                    self._count += 1
                    return self._start
                case RangeMode.RANDOM:
                    self._count += 1
                    return round(uniform(self._start, self._end), 3)
                case RangeMode.SEQUENCE:
                    self._index += self._delta
                    if self._index >= self._end:
                        self._index = self._start - self._delta
                        self._count += 1
                        return self._end
                    self._count += 1
                    return self._index
                case RangeMode.ONE:
                    self._count += 1
                    return self._start
        except Exception as e:
            raise e
        finally:
            # print(f"{self._delay}s")
            time.sleep(self._delay)

    def spin(self):
        try:
            n = self.__next__()
        except StopIteration:
            try:
                self.reset()
                n = self.__next__()
            except Exception as e:
                raise e
        return n

    def next(self):
        return self.__next__()

    def stop(self):
        self.mode = RangeMode.STOP

    def resume(self):
        self.mode = self._mode

    def reset(self, start=None, end=None, delta=None, mode=None):
        for key, value in locals().items():
            if key == "self":
                continue
            if value is not None:
                setattr(self, f"_{key}", float(value))
                if key == "mode":
                    self.mode = value
        self._index = self._start - self._delta
        self._count = 0
        self.resume()


class Ranger:
    def __init__(
        self,
        ranges="900-935_0.1,r:3850-4075_10;1",
        maxiter=None,
        sleep_secs=0.0,
        entropy=False,
    ):
        self.ranges = []
        self._ranges = ranges
        self._rindex = 0
        self._delay = sleep_secs
        self._random = entropy

        for r in ranges.split(","):
            delta = 0.1
            rmode = RangeMode.SEQUENCE

            if self._random:
                rmode = RangeMode.RANDOM

            if ";" in r:
                r, sleep_time = r.split(";")
                self._delay = float(sleep_time)

            if "r:" in r:
                r = r.replace("r:", "")
                rmode = RangeMode.RANDOM

            if "_" in r:
                r, delta = r.split("_")
                if "." not in delta:
                    delta = delta + ".0"
                delta = float(delta)

            if "-" in r:
                start, end = r.split("-")
                # print(f"start: {start}, end: {end}")

                if "." not in start:
                    start = start + ".0"
                if "." not in end:
                    end = end + ".0"

                rstart = float(start)
                rend = float(end)

                self.ranges.append(
                    Range(rstart, rend, delta, rmode, maxiter, self._delay)
                )
            else:
                self.ranges.append(
                    Range(
                        rstart=float(r),
                        rend=float(r),
                        rmode=RangeMode.ONE,
                        maxiter=1,
                        sleep_secs=self._delay,
                    )
                )

        for r in self.ranges:
            if not r:
                self.ranges.remove(r)
            print(r)

    def __len__(self):
        ct = 0
        for r in self.ranges:
            ct += len(r)
        return ct

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.ranges) == 0:
            raise StopIteration

        if self._rindex >= len(self.ranges):
            for r in self.ranges:
                r.reset()
            self._rindex = 0
            raise StopIteration

        try:
            n = self.ranges[self._rindex].next()
        except StopIteration:
            self.ranges[self._rindex].reset()
            if self._random:
                shuffle(self.ranges)
            self._rindex += 1
            n = self.__next__()

        if n is None:
            raise StopIteration

        return round(n, 3)
