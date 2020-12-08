import logging
import numpy as np

from PyQt5.QtCore import QThread

import nidaqmx
from nidaqmx import *
from nidaqmx.constants import *
from hardware.analog_input import BaseAnalogInput


class AnalogInClockOut(QThread, BaseAnalogInput):

    _min_voltage = -2.5
    _max_voltage = 2.5

    def __init__(self):         #Creates a new task and sets name to 'self'
        super().__init__()
        self._set_lockin_channel()
        self._set_ai_channel()

    def _create_tasks(self):
        self._ai_task = nidaqmx.task.Task()
        self._trigger_out_task = nidaqmx.task.Task()
        self._lockin_task = nidaqmx.task.Task()

    def _setInputChannels(self, input_channels):
        self._set_ai_channel(input_channels)

    def setLockingFrequency(self, lockin_frequency):
        self.lockin_frequency = lockin_frequency

    def _set_ai_channel(self, ai_channel="/dev4/ai0:1"):
        self._ai_channel = ai_channel

    def _set_lockin_channel(self, lockin_channel=""):
        self._lockin_channel = lockin_channel

    def _setAnalogInputRange(self, min_voltage, max_voltage):
        self._min_voltage = min_voltage
        self._max_voltage = max_voltage

    def _configure_ai_task(self):
        try:
            self._ai_channels = ",".join([self._ai_channel, self._lockin_channel])
            self._ai_chan = self._ai_task.ai_channels.add_ai_voltage_chan(self._ai_channels)
            self._ai_task.triggers.start_trigger.cfg_dig_edge_start_trig("/dev4/PFI0", trigger_edge=Edge.RISING) # starts qcquiring or generating samples on a rising edge of a digital sample
            self._ai_task.timing.cfg_samp_clk_timing(rate=self._samplerate, samps_per_chan=self._N_samples, sample_mode=AcquisitionType.FINITE)     #source of the sample clock, sample rate and the number of samples to acquire
            self._ai_chan.ai_term_cfg = TerminalConfiguration.RSE
            self._ai_chan.ai_min = self._min_voltage
            self._ai_chan.ai_max = self._max_voltage
        except Exception as err:
            logging.getLogger().debug(err)
            raise


    def _configure_trigger_task(self):
        try:
            frequency = 1./self._seconds_per_point
            self._co_chan = self._trigger_out_task.co_channels.add_co_pulse_chan_freq("/dev4/Ctr0", idle_state=Level.LOW, initial_delay=0.0, freq=frequency, duty_cycle=0.1)
            self._co_chan.co_pulse_term = "/dev4/PFI0"
            self._trigger_out_task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.CONTINUOUS)       #stes the number of acquired samples
        except Exception as err:
            logging.getLogger().debug(err)
            raise

    def _configure_lockin_task(self):
        try:
            if self._lockin_channel != "":
                self._lockin_co_chan = self._lockin_task.co_channels.add_co_pulse_chan_freq("/dev4/Ctr1", idle_state=Level.LOW, initial_delay=0.0, freq=self.lockin_frequency, duty_cycle=0.5)
                self._lockin_co_chan.co_pulse_term = "/dev4/PFI1"
                self._lockin_task.triggers.start_trigger.cfg_dig_edge_start_trig("/dev4/PFI0", trigger_edge=Edge.RISING)
                self._lockin_task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.CONTINUOUS)
            else:
                self._lockin_do_chan = self._lockin_task.do_channels.add_do_chan("/dev4/PFI1")
                self._lockin_task.triggers.start_trigger.cfg_dig_edge_start_trig("/dev4/PFI0", trigger_edge=Edge.RISING)
                self._lockin_task.write(True)
        except Exception as err:
            logging.getLogger().exception(err)

    def _destroy_tasks(self):
        if hasattr(self, "_ai_task"):
            self._ai_task.close()
            del self._ai_task
        if hasattr(self, "_trigger_out_task"):
            self._trigger_out_task.close()
            del self._trigger_out_task
        if hasattr(self, "_lockin_task"):
            self._lockin_task.close()
            del self._lockin_task


    def __del__(self):
        self._destroy_tasks()

    def configure(self, samplerate, seconds_per_point, n_frequencies):
        try:
            self._samplerate = samplerate
            self._seconds_per_point = seconds_per_point
            self._n_frequencies = n_frequencies
            self._N_samples = int(self._seconds_per_point * self._samplerate * self._n_frequencies)

            self._create_tasks()
            self._configure_ai_task()
            self._configure_trigger_task()
            self._configure_lockin_task()
        except Exception as err:
            logging.getLogger().exception(err)

    def stopTasks(self):
        self._destroy_tasks()

    def run(self):
        try:
            self._ai_task.start()
            self._lockin_task.start()
            self._trigger_out_task.start()
            #m# TIMEOUT_S = self._N_samples/self._samplerate + 1
            TIMEOUT_S = 5.*self._N_samples/self._samplerate
            self._ai_task.wait_until_done(TIMEOUT_S)
            self._data = np.array(self._ai_task.read(number_of_samples_per_channel=self._N_samples))

            self._ai_task.stop()
            self._lockin_task.stop() #m#
            self._trigger_out_task.stop()
        except Exception as err:
            logging.getLogger().exception(err)

    def getData(self):
        return self._data
