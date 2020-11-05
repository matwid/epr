"""EPR startup script"""
import os
import inspect
from traits.api         import HasTraits, Instance, SingletonHasTraits, Range, on_trait_change
from traitsui.api       import View, Item, Group, HGroup, VGroup
from traits.api         import Button
import logging, logging.handlers


path = os.path.dirname(inspect.getfile(inspect.currentframe()))

# First thing we do is start the logger
file_handler = logging.handlers.TimedRotatingFileHandler(path+'/log/log.txt', 'W6') # start new file every sunday, keeping all the old ones 
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(module)s.%(funcName)s - %(levelname)s - %(message)s"))
file_handler.setLevel(logging.DEBUG)
stream_handler=logging.StreamHandler()
stream_handler.setLevel(logging.INFO) # we don't want the console to be swamped with debug messages
logging.getLogger().addHandler(file_handler)
logging.getLogger().addHandler(stream_handler) # also log to stderr
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().info('Starting logger.')

# start the JobManager
from tools import emod
emod.JobManager().start()

# start the CronDaemon
from tools import cron
cron.CronDaemon().start()

# define a shutdown function
from tools.utility import StoppableThread
import threading

def shutdown(timeout=1.0):
    """Terminate all threads."""
    cron.CronDaemon().stop()
    emod.JobManager().stop()
    for t in threading.enumerate():
        if isinstance(t, StoppableThread):
            t.stop(timeout=timeout)

# numerical classes that are used everywhere
import numpy as np 

#########################################
# hardware
#########################################

from hardware.dummy import Nidaq as nidaq


# create hardware backends
epr_counter = nidaq.AnalogOutBurst(ao_chan=0, co_dev=1)

#########################################
# create measurements
#########################################

import measurements.epr 
epr = measurements.epr.EPR()

#########################################
# fire up the GUI
#########################################


epr.configure_traits()


