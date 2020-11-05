import numpy as np


from tools.chaco_addons import SavePlot as Plot, SaveTool

from traits.api       import SingletonHasTraits, Instance, Range, Bool, Array, Str, Enum, Button, on_trait_change, Trait, Float
from traitsui.api     import View, Item, Group, HGroup, VGroup, VSplit, Tabbed, EnumEditor
from enable.api       import ComponentEditor, Component
from chaco.api        import PlotAxis, CMapImagePlot, ColorBar, LinearMapper, ArrayPlotData, Spectral
import logging

from tools.emod import ManagedJob
from tools.utility import GetSetItemsMixin, timestamp
import time

class EPR( ManagedJob, GetSetItemsMixin ):
    """
    Measures EPR data.
    
      last modified
    """
    
    v_begin           = Range(low=-200., high=200.,    value=0.,    desc='begin [V]',  label='begin [V]',   mode='text', auto_set=False, enter_set=True)
    v_end             = Range(low=-200., high=200.,    value=5.,      desc='end [V]',    label='end [V]',     mode='text', auto_set=False, enter_set=True)
    v_delta           = Range(low=-200., high=200.,       value=.5,     desc='delta [V]',  label='delta [V]',   mode='text', auto_set=False, enter_set=True)
    v_divisions       = Range(low=0, high=1e6,       value=100,     desc='divisions [#]',  label='divisions [#]',   mode='text', auto_set=False, enter_set=True)
    v_reset           = Float(default_value=0, label='reset voltage')
    allow_high_voltage= Bool(False, desc='allow high voltage',  label='allow high voltage',)
    hysterese         = Bool(False, desc='performs forward and backward scan',  label='hysterese',)
    
    seconds_per_point = Float(default_value=.1, desc='Seconds per point', label='Seconds per point', mode='text', auto_set=False, enter_set=True)
    proceed           = Float(default_value=0.0, label='proceed [%]')
    time_remain       = Float(default_value=0.0, label='remaining time [min]')

    scale             = Enum('lin','log',value='log', desc='scale')
    plot_tpe          = Enum('line', 'scatter')
    
    voltage           = Array()#for plot1 & 2 and for saving
    current           = Array()#for saving only
    counts            = Array()#for saving only
    y_data            = Array()#plot1 y-data
    y_data2           = Array()#plot2 y-data
    x_data            = Array()
    total_length      = Float()#for time proceed only
    measured_current  = Float()#to display currently measured current
     
    plot_data         = Instance( ArrayPlotData )
    plot              = Instance( Plot )
    plot_data2        = Instance( ArrayPlotData )
    plot2             = Instance( Plot )

    max_current = Float(default_value=10e-3, label='max current')

    get_set_items=['__doc__', 'v_begin', 'v_end', 'v_delta', 'hysterese','seconds_per_point', 'voltage', 'current', 'counts' ]

    traits_view = View(VGroup(HGroup(Item('submit_button',   show_label=False),
                                     Item('remove_button',   show_label=False),
                                     Item('priority'),
                                     Item('state',       style='readonly'),
                                     Item('proceed',     show_label=True, style='readonly',format_str='%.f'),
                                     Item('time_remain', show_label = True, style='readonly',format_str='%.f'),
                                     Item('measured_current', show_label = True, style='readonly',format_str='%.f'),
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
                                     Item('hysterese',  enabled_when='scale != "log"')
                                     ),
                              HGroup(Item('seconds_per_point'),
                                     Item('max_current',enabled_when='scale != "run"'),
                                     Item('allow_high_voltage',enabled_when='scale != "run"'),
                                     #Item('plot_tpe')
                                     ),
                              Item('plot', editor=ComponentEditor(), show_label=False, resizable=True),
                              Item('plot2', editor=ComponentEditor(), show_label=False, resizable=True),
                              ),
                       title='ivcurve', buttons=[], resizable=True
                       )

    
    def __init__(self, time_tagger, keithley,  **kwargs):
        super(Ivcurve, self).__init__(**kwargs)
        self.time_tagger = time_tagger
        self.keithley = keithley
        
        self._create_plot()
        self._create_plot2()
        self.on_trait_change(self._update_index,    'x_data',    dispatch='ui')
        self.on_trait_change(self._update_value,    'y_data',    dispatch='ui')
        self.on_trait_change(self._update_index2,   'x_data',    dispatch='ui')
        self.on_trait_change(self._update_value2,  'y_data2',    dispatch='ui')
        
    def _run(self):

        try:
            self.keithley.service_request_for_data_ready()
            self.state='run'
            
            #prepare empty arrays here, for eg a second run
            self.voltage = self.generate_voltage()
            self.x_data  = np.array(())
            self.y_data  = np.array(())
            self.y_data2 = np.array(())

            total_length = len(np.arange(self.v_begin, self.v_end, self.v_delta))
            
            #Prepare counter
            counter_0 = self.time_tagger.Countrate(0)
            counter_1 = self.time_tagger.Countrate(1)
         

            for i,v in enumerate(self.voltage):



                # set the voltage
                self.keithley.set_voltage(channel=1,voltage=v, max_current=self.max_current)                 
                
                #clear counters             
                counter_0.clear()
                counter_1.clear()                
                
                #stop routine
                self.thread.stop_request.wait(self.seconds_per_point)
                if self.thread.stop_request.isSet():
                    logging.getLogger().debug('Caught stop signal. Exiting.')
                    self.state = 'idle'
                    break            
                
                #set integration time
                self.measured_current = self.keithley.get_meancurrent(channel=1,t=self.seconds_per_point)*1000
                time.sleep(self.seconds_per_point)
                
                #get data                
                measured_counts       = counter_0.getData() + counter_1.getData()                
                #self.measured_current = self.keithley.get_current(channel=1)*1000

                              
                #set the plot data
                self.y_data2          = np.append(self.y_data2, measured_counts)
                self.y_data           = np.append(self.y_data,self.measured_current)
                self.x_data           = np.append(self.x_data,v)

                # update proceeding time
                self.update_time_proceed(i,total_length)
            
            else:
                self.update_time_proceed(total_length,total_length)
                self.state='done'

            del counter_0
            del counter_1
                        
        except:
            logging.getLogger().exception('Error in ivcurve.')
            self.state = 'error'

            
        finally:
            self.set_data_for_get_set_items()
            self.reset_keithley()
            self.state = 'done'
    #################################################################
    # Helper Methods
    #################################################################
    def set_data_for_get_set_items(self):
        """sets the data for saving"""
        self.current = self.y_data
        self.counts  = self.y_data2


    def update_time_proceed(self,i,total_length):
        """simply updates the time elapsed"""
        self.proceed    =(float(i)/(float(total_length)))*100
        self.time_remain=((self.seconds_per_point*total_length)-(i*self.seconds_per_point))/60




    #################################################################
    # PLOT DEFINITIONS
    #################################################################

    def _create_plot(self):
        plot_data = ArrayPlotData(x_data=np.array(()), y_data=np.array(()),)
        plot = Plot(plot_data, padding=8, padding_left=64, padding_bottom=64)
        plot.plot(('x_data','y_data'), color='blue', type='line')
        plot.index_axis.title = 'Diode voltage [V]'
        plot.value_axis.title = 'Current [mA]'
        plot.tools.append(SaveTool(plot))   
        self.plot_data = plot_data
        self.plot = plot

    def _update_index(self, new):
        self.plot_data.set_data('x_data', new)
        #if self.scale == 'lin':
        #    self.plot.index_scale = 'linear'

        #if self.scale == 'log':
        #    self.plot.index_scale = 'log'
        
    def _update_value(self, new):
        self.plot_data.set_data('y_data', new)

    def save_plot(self, filename):
        save_figure(self.plot, filename)

    def _create_plot2(self):
        plot_data2 = ArrayPlotData(x_data=np.array(()), y_data2=np.array(()),)
        plot2 = Plot(plot_data2, padding=8, padding_left=64, padding_bottom=64)
        plot2.plot(('x_data','y_data2'), color='blue', type='line')
        plot2.index_axis.title = 'Diode voltage [V]'
        plot2.value_axis.title = 'Photon counts [cts]'
        plot2.tools.append(SaveTool(plot2))   
        self.plot_data2 = plot_data2
        self.plot2 = plot2

    def _update_index2(self, new):
        self.plot_data2.set_data('x_data', new)
        #if self.scale == 'lin':
        #    self.plot.index_scale = 'linear'

        #if self.scale == 'log':
        #    self.plot.index_scale = 'log'
        
    def _update_value2(self, new):
        self.plot_data2.set_data('y_data2', new*1e-3)

    def save_plot(self, filename):
        save_figure(self.plot, filename)
    def save_all(self, filename):
        self.plot.save(filename+'_i_v.png')
        self.plot2.save(filename+'_i_counts.png')
        self.save(filename+'.pys')
        self.save(filename+'-ACSII.pys')
        np.savetxt(filename+'_i_v.txt',np.transpose((self.voltage,self.y_data)))
        np.savetxt(filename+'_i_counts.txt',np.transpose((self.voltage,self.y_data2)))

    def generate_voltage(self):
        if self.scale == 'lin':
            mesh = np.arange(self.v_begin, self.v_end, self.v_delta)
            if self.hysterese:
                k= mesh[::-1]#reverse mesh
                mesh = np.append(mesh,k)
            return mesh
        if self.scale == 'log':
            difference = self.v_end-self.v_begin
            temp_mesh = np.logspace(0, np.log10(np.abs(difference)), self.v_divisions, base=10.0)
            mesh = temp_mesh - np.abs(difference)
            return mesh


    

if __name__=='__main__':
    epr = EPR(time_tagger, keithley)
    epr.edit_traits()
    
