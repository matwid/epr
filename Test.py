import nidaqmx
import time





def _set_bias(v_bias):
    """sets an  analog output"""
    with nidaqmx.Task() as analog_output_task:
        analog_output_task.ao_channels.add_ao_voltage_chan("Dev1/ao0","output_channel")
        analog_output_task.start
        analog_output_task.write(v_bias)
        #time.sleep(10)
        analog_output_task.stop
