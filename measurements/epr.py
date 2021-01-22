import numpy as np


from tools.chaco_addons import SavePlot as Plot, SaveTool

from traits.api       import SingletonHasTraits, Instance, Range, Bool, Array, Str, Enum, Button, on_trait_change, Trait, Float
from traitsui.api     import View, Item, Group, HGroup, VGroup, VSplit, Tabbed, EnumEditor
from enable.api       import ComponentEditor, Component
from chaco.api        import PlotAxis, CMapImagePlot, ColorBar, LinearMapper, ArrayPlotData, Spectral
import logging

from tools.emod import FreeJob
from tools.utility import GetSetItemsMixin, timestamp
import time


import threading



class EPR( FreeJob, GetSetItemsMixin ):
    """
    Measures EPR data.

      last modified
    """
    """
    #Test setting for time saving reasons ###################################################################################################################
    v_begin           = Range(low=0., high=10.,    value=0,    desc='begin [V]',  label='begin [V]',   mode='text', auto_set=False, enter_set=True)
    v_end             = Range(low=0.001, high=10.,    value=1,      desc='end [V]',    label='end [V]',     mode='text', auto_set=False, enter_set=True)
    v_bias            = Float(default_value=0,label=' ')
    v_delta           = Range(low=0., high=10.,       value=.1,     desc='delta [V]',  label='delta [V]',   mode='text', auto_set=False, enter_set=True)
    
    x_axis           = Enum('control voltage','hall voltage','logIn voltage')
    y_axis           = Enum('logIn voltage','control voltage', 'hall voltage')
    #################################################################################################################################################
    """

    
    v_begin           = Range(low=0., high=10.,    value=4.4,    desc='begin [V]',  label='begin [V]',   mode='text', auto_set=False, enter_set=True)
    v_end             = Range(low=0.001, high=10.,    value=4.7,      desc='end [V]',    label='end [V]',     mode='text', auto_set=False, enter_set=True)
    v_bias            = Float(default_value=4.5,label=' ')
    v_delta           = Range(low=0., high=10.,       value=.001,     desc='delta [V]',  label='delta [V]',   mode='text', auto_set=False, enter_set=True)

    x_axis           = Enum('not set','control voltage', 'hall voltage','logIn voltage')
    y_axis           = Enum('not set','control voltage', 'hall voltage','logIn voltage')
      



    v_divisions       = Range(low=0, high=1e6,       value=100,     desc='divisions [#]',  label='divisions [#]',   mode='text', auto_set=False, enter_set=True)
    v_reset           = Float(default_value=0, label='reset voltage')

    seconds_per_point = Float(default_value=.001, desc='Seconds per point', label='Seconds per point', mode='text', auto_set=False, enter_set=True)
    proceed           = Float(default_value=0.0, label='proceed [%]')
    time_remain       = Float(default_value=0.0, label='remaining time [min]')

    scale             = Enum('lin','log',value='log', desc='scale')
    plot_tpe          = Enum('line', 'scatter')


    voltage           = Array()#for saving only
    hall_voltage      = Array()#
    lockin_data       = Array()#
    login_V_data      = Array()#    
    hall_V_data       = Array()#
    control_V_data    = Array()#

    total_length      = Float()#for time proceed only

    x_data_plot       = Array()#for ploting
    y_data_plot       = Array()#

    plot_data         = Instance( ArrayPlotData )
    plot              = Instance( Plot )

    bias_button = Button(label='set bias', show_label=False)
    bias_measured_button =  Button(label='measuerd bias', show_label=False)
    bias_value = Float()


    max_current = Float(default_value=10e-3, label='max current')

    get_set_items=['__doc__', 'v_begin', 'v_end', 'v_delta', 'seconds_per_point', 'v_bias', 'voltage', 'hall_voltage', 'lockin_data' ]

    traits_view = View(VGroup(HGroup(Item('start_button',   show_label=False),
                                     Item('stop_button',   show_label=False),
                                     Item('state',       style='readonly'),
                                     Item('proceed',     show_label=True, style='readonly',format_str='%.f'),
                                     Item('time_remain', show_label = True, style='readonly',format_str='%.f'),

                                     ),
                              HGroup(Item('filename',    springy=True),
                                     Item('save_button', show_label=False),
                                     Item('load_button', show_label=False)
                                     ),
                              HGroup(Item('v_begin'),
                                     Item('v_end'),
                                     Item('v_delta',    enabled_when='scale != "log"'),
                                     Item('v_divisions',enabled_when='scale != "lin"'),
                                     Item('scale',      width=-80, enabled_when='state != "run"'),

                                     ),
                              HGroup(Item('seconds_per_point'),
                                     Item('max_current',enabled_when='scale != "run"'),

                                     Item('plot_tpe')
                                     ),
                              HGroup(Item('bias_button', show_label=False),
                                     Item('v_bias', show_label=False),
                                     Item('bias_measured_button',show_label=False),
                                     Item('bias_value'),
                                     Item('x_axis'),
                                     Item('y_axis')
                                     ),                                     
                              Item('plot', editor=ComponentEditor(), show_label=False, resizable=True),

                              ),
                       title='Electron Paramagnetic Resonance (EPR) is equal to Electron Spin Resonace (ESR)', buttons=[], resizable=True
                    )

    def __init__(self, task_in, task_out,  **kwargs):
        super(EPR, self).__init__(**kwargs)

        self._create_plot()
        self.task_in = task_in
        
        self.task_out = task_out
        self.on_trait_change(self._update_index,    'x_data_plot',    dispatch='ui')
        self.on_trait_change(self._update_value,    'y_data_plot',    dispatch='ui')

        self.on_trait_change(self._update_naming_x,    'x_axis',    dispatch='ui')
        self.on_trait_change(self._update_naming_y,    'y_axis',    dispatch='ui')
        
        self.task_out.start()

        self.first_bias = 'true'
        self.bias_button_was_fired = 'false'
        self.bias_set = 0

    def _run(self):
        #self.task_in = nidaqmx.Task()
        #self.task_out = nidaqmx.Task()

        #self.task_in.ai_channels.add_ai_voltage_chan("Dev1/ai0")
        #self.task_out.ao_channels.add_ao_voltage_chan("Dev1/ao0","output_channel")
        self.measurment_stopped = 'false'
        self.task_in.start()
        

        """
        self.plot_data_on_x()
        self.plot_data_on_x()
        """
        try:
            self.state='run'

            #prepare empty arrays here, for eg a second run
            self.voltage = self.generate_voltage()
            self.control_V_data  = np.array(())
            self.login_V_data  = np.array(())
            self.hall_V_data  = np.array(())
            self.lockin_data  = np.array(())
            self.hall_voltage  = np.array(())

            total_length = len(np.arange(self.v_begin, self.v_end, self.v_delta))

            self.increase_voltage()

            for i,v in enumerate(self.voltage): 
                self.measurment_finished = 'false' # Stop button only works while loop is active 

                #stop routine
                self.thread.stop_request.wait(self.seconds_per_point)
                if self.thread.stop_request.isSet():
                    logging.getLogger().debug('Caught stop signal. Exiting.')
                    self.state = 'idle'
                    break
                
                self.task_out.write(v)
                self.current_voltage = v 
                
                #set integration time
                time.sleep(self.seconds_per_point)

                #get data
                measured_data = self.task_in.read(50)
                measured_voltage = np.mean(measured_data[0])
                lockin_data = np.mean(measured_data[1])
                self.bias_value = measured_voltage

                #lockin_data = self.task_lockin.read()

                # fills the storage arrays with the measured data 
                self.hall_V_data          = np.append(self.hall_V_data,     measured_voltage)
                self.login_V_data         = np.append(self.login_V_data,    lockin_data)
                self.control_V_data       = np.append(self.control_V_data,  v)
                
                # writes the chosen data into the plot arrays
                self.plot_data_on_x()
                self.plot_data_on_y()
                
                # update proceeding time
                self.update_time_proceed(i,total_length)
                
            else:
                self.update_time_proceed(total_length,total_length)
                self.state='done'


        except:
            logging.getLogger().exception('Error in EPR measurement.')
            self.decrease_voltage()
            self.task_out.stop()
            self.task_in.stop()
            self.state = 'error'

        finally:
            self.measurment_finished = 'true'
            if self.measurment_stopped is 'false':
                self.decrease_voltage()
            self.set_data_for_get_set_items()
            self.task_in.stop()
            self.task_out.stop()

            self.state = 'done'

    #################################################################
    # Helper Methods
    #################################################################


    def _bias_button_fired(self): #slowly increase/decrease of voltage, while using the bias button
        if self.first_bias is 'true':
            voltage_array = np.arange(0.01,self.v_bias, 0.001) 
            for i,val in enumerate(voltage_array):
                self.task_out.write(val) 
                time.sleep(0.001)  
            self.first_bias = 'false'
            self.bias_set = self.val
        else:
            if self.bias_set < self.v_bias:
                voltage_array = np.arange(self.bias_set,self.v_bias, 0.001) 
                for i,val in enumerate(voltage_array):
                    self.task_out.write(val) 
                    time.sleep(0.001)
                self.bias_set = val
            else:
                voltage_array = np.arange(self.v_bias,self.bias_set, 0.001) 
                voltage_array = np.flipud(voltage_array)
                for i,val in enumerate(voltage_array):
                    self.task_out.write(val) 
                    time.sleep(0.001)
                self.bias_set = val
        self.bias_button_was_fired = 'true'

       
    def set_data_for_get_set_items(self):
        """sets the data for saving"""
        self.hall_voltage = self.login_V_data
        self.lockin_data  = self.hall_V_data

    def _bias_measured_button_fired(self):
        measured_data = self.task_in.read()
        self.bias_value = measured_data[0]
     
 
    def update_time_proceed(self,i,total_length):
        """simply updates the time elapsed"""
        self.proceed    =(float(i)/(float(total_length)))*100
        self.time_remain=((self.seconds_per_point*total_length)-(i*self.seconds_per_point))/60


    def increase_voltage(self): #makes sure, that the voltage increases slowly 
        if self.bias_button_was_fired is 'true':
            voltage_array = np.arange(self.v_bias,self.v_begin, 0.001)
            for i,val in enumerate(voltage_array):
                self.task_out.write(val) 
                time.sleep(0.001)
        else:
            voltage_array = np.arange(0.001,self.v_begin, 0.01)
            for i,val in enumerate(voltage_array):
                self.task_out.write(val) 
                time.sleep(0.001)


    def decrease_voltage(self): #makes sure, that the voltage decreases slowly 
        if self.bias_button_was_fired is 'true' or self.measurment_stopped is 'true':
            voltage_array = np.arange(self.v_bias,self.current_voltage, 0.01) 
            voltage_array = np.flipud(voltage_array)
            for i,val in enumerate(voltage_array):
                self.task_out.write(val) 
                time.sleep(0.01)
        else:
            voltage_array = np.arange(0.001,self.current_voltage, 0.01) 
            voltage_array = np.flipud(voltage_array)
            for i,val in enumerate(voltage_array):
                self.task_out.write(val) 
                time.sleep(0.01)


    #################################################################
    # PLOT DEFINITIONS
    #################################################################

    def _create_plot(self):
        plot_data = ArrayPlotData(x_data_plot=np.array(()), y_data_plot=np.array(()))
        plot = Plot(plot_data, padding=8, padding_left=64, padding_bottom=64)
        plot.plot(('x_data_plot','y_data_plot'), color='blue', type='line')
        plot.tools.append(SaveTool(plot))
        self.plot_data = plot_data
        self.plot = plot


    def _update_naming_x(self): 
        if self.x_axis == 'control voltage':
            self.plot.index_axis.title = 'control voltage [V]'
            return
        elif self.x_axis == 'hall voltage':
            self.plot.index_axis.title = 'hall voltage [V]'
            return
        elif self.x_axis == 'logIn voltage':
            self.plot.index_axis.title = 'logIn voltage [V]'
            return

    def _update_naming_y(self):   
        if self.y_axis == 'control voltage':
            self.plot.value_axis.title = 'control voltage [V]'
            return
        elif self.y_axis == 'hall voltage':
            self.plot.value_axis.title = 'hall voltage [V]'
            return
        elif self.y_axis == 'logIn voltage':
            self.plot.value_axis.title = 'logIn voltage [V]'
            return   


    def _update_index(self, new):
        
        self.plot_data_on_x()
        self.plot_data.set_data('x_data_plot', new)


    def _update_value(self, new):
        self.plot_data_on_y()
        self.plot_data.set_data('y_data_plot', new)
   
    
    def save_plot(self, filename):
        save_figure(self.plot, filename)


    def save_all(self, filename):
        self.save(filename+'.pys')
        self.save(filename+'-ACSII.pys')
        np.savetxt(filename+'.txt',(self.voltage,self.login_V_data))
    

    def generate_voltage(self):
        if self.scale == 'lin':
            mesh = np.arange(self.v_begin, self.v_end, self.v_delta)
            return mesh
        if self.scale == 'log':
            difference = self.v_end-self.v_begin
            temp_mesh = np.logspace(0, np.log10(np.abs(difference)), self.v_divisions, base=10.0)
            mesh = temp_mesh - np.abs(difference)
            return mesh

    def plot_data_on_x(self):
        if self.x_axis == 'control voltage':
            self.x_data_plot = self.control_V_data
            return
        elif self.x_axis == 'hall voltage':
            self.x_data_plot = self.hall_V_data
            return
        elif self.x_axis == 'logIn voltage':
            self.x_data_plot =  self.login_V_data
            return


    def plot_data_on_y(self):    
        if self.y_axis == 'control voltage':
            self.y_data_plot = self.control_V_data
            return
        elif self.y_axis == 'hall voltage':
            self.y_data_plot = self.hall_V_data
            return
        elif self.y_axis == 'logIn voltage':
            self.y_data_plot =  self.login_V_data
            return

if __name__=='__main__':
    epr = EPR()
    epr.configure_traits()
