"""
Dummy hardware classes for testing.
"""

import numpy as np
import logging
import time
import random


class Nidaq():


    class AnalogOutBurst():

        """
        Analog output a single run waveform or single point.
        """

        def __init__(self, ao_chan, co_dev, ao_range=(-10,10), duty_cycle=0.96):
            ao_task = None
            co_task = None
            self.ao_task = ao_task
            self.co_task = co_task
            self.co_dev = co_dev
            self.duty_cycle = duty_cycle
            self.n_samples = None
            self.seconds_per_point = None

        def configure(self, n_samples, seconds_per_point):
            pass


        def point(self, voltage2):
            pass

        def line(self, voltage, seconds_per_point):
            """Output a waveform and perform synchronous counting."""
            pass



    class AnalogInClockOut():

        """
        Analog input a single run waveform or single point.
        """

        def __init__(self, ao_chan, co_dev, ao_range=(-10,10), duty_cycle=0.96):
            ao_task = None
            co_task = None
            self.ao_task = ao_task
            self.co_task = co_task
            self.co_dev = co_dev
            self.duty_cycle = duty_cycle
            self.n_samples = None
            self.seconds_per_point = None

        def configure(self, n_samples, seconds_per_point):
            pass


        def point(self, voltage2):
            pass

        def line(self, voltage, seconds_per_point):
            """Output a waveform and perform synchronous counting."""
            pass
