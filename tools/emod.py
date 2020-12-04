"""
The execution model.
"""

import threading
import logging

from tools.utility import Singleton, StoppableThread, timestamp
from functools import reduce
from functools import cmp_to_key

from traits.api import HasTraits, Instance, Enum, Range, Button
from traitsui.api import View, Item, HGroup

# ToDo: maybe add auto_start functionality of the JobManager (e.g. self.start within submit() method)?

class Job( HasTraits ):

    """
    Defines a job.

    Methods:

        start():        starts the job
        stop(timeout):  stops the job
        _run():         actual function that is run in a thread

    Data:

        priority:   priority of the job (used by a job manager to schedule the job)
        state:      shows the current state of the job, 'idle', 'run' or 'wait'

      In the current execution model, a job should be re-startable.
    I.e., when a job is stopped before it is finished, upon next
    start, the work should be continued e.g. previously acquired
    data should be kept and accumulated.

      It is the user's task to ensure that previous data is
    handled correctly and to decide when a job should be continued
    and when it should be restarted as a new measurement.

      A job can be in one of three states 'idle': doing nothing,
    'run': running, 'wait': waiting to be executed. The latter state
    is typically set by a Job manager to show that the job is
    scheduled for execution. The
    """

    priority = Range(low=0, high=10, value=0, desc='priority of the job', label='priority', mode='text', auto_set=False, enter_set=True)

    state = Enum('idle', 'run', 'wait', 'done', 'error') # only for display. Shows the state of the job. 'idle': not submitted, 'run': running, 'wait':in queue

    thread = Instance( StoppableThread, factory=StoppableThread )

    def start(self):
        """Start the thread."""
        if self.thread.is_alive():
            return
        self.thread = StoppableThread(target = self._run, name=self.__class__.__name__ + timestamp())
        self.thread.start()

    def stop(self, timeout=None):
        """Stop the thread."""
        self.thread.stop(timeout=timeout)

    def _run(self):
        """Method that is run in a thread."""
        try:
            self.state='run'
            while(True):
                #logging.getLogger().debug("Yeah, still taking data like the LHC!")
                self.thread.stop_request.wait(1.0) # little trick to have a long (1 s) refresh interval but still react immediately to a stop request
                if self.thread.stop_request.isSet():
                    logging.getLogger().debug('Received stop signal. Returning from thread.')
                    break
            if True:
                self.state='idle'
            else:
                self.state='done'
        except:
            logging.getLogger().exception('Error in job.')
            self.state='error'
        finally:
            logging.getLogger().debug('Turning off all instruments.')



class FreeJob( Job ):

    """
    Job with buttons that start the job without the JobManager.

    GUI:

        start_button:    calls start()
        stop_button:     calls stop()

    """

    start_button = Button(label='start', desc='Starts the measurement.')
    stop_button  = Button(label='stop',  desc='Stops the measurement.')

    def _start_button_fired(self):
        """React to submit button. Submit the Job."""
        self.start()

    def _stop_button_fired(self):
        """React to remove button. Remove the Job."""
        self.stop()

    traits_view=View(HGroup(Item('start_button', show_label=False),
                            Item('stop_button', show_label=False),
                            Item('priority'),
                            Item('state', style='readonly'),),
                     resizable=True)





if __name__ == '__main__':

    import time
    time.sleep(0.1)
    j = Job()
    j.priority = 1
    JobManager().submit(j)
