import numpy as np
import logging

class BaseAnalogInput():

    def __init__(self):
        pass

    def setSamplerate(self, samplerate):
        if samplerate <= 0:
            raise ValueError("Samplerate must be larger than 0.")   
        self._samplerate = samplerate
        return self._setSamplerate(samplerate)

    def _setSamplerate(self, samplerate):
        raise NotImplementedError

    def setNumberOfSamples(self, n_samples):
        if n_samples < 1:
            raise ValueError("Number of samples must be larger than 1.")   
        return self._setNumberOfSamples(n_samples)    

    def _setNumberOfSamples(self, n_samples): 
        raise NotImplementedError
        self._n_samples = n_samples
    
    def setAnalogInputRange(self, min_voltage, max_voltage):
        self._min_voltage = min_voltage
        self._max_voltage = max_voltage
        return self._setAnalogInputRange(min_voltage, max_voltage)
        
    def _setAnalogInputRange(min_voltage, max_voltage):
        raise NotImplementedError 

    def setInputChannels(self, input_channels):
        return self._setInputChannels(input_channels)

    def _setInputChannels(self, input_channels):
        raise NotImplementedError

    def setTriggerSource(self, trigger_source):
        return self._setTriggerSource(trigger_source)

    def _setTriggerSource(self, trigger_source):
        raise NotImplementedError

    def singleSweep(self):
        return self._singleSweep()

    def _singleSweep(self):
        raise NotImplementedError

    def getData(self):
        return self._getData()

    def _getData(self):
        raise NotImplementedError   

class MockAnalogInput(BaseAnalogInput):

    TIMEOUT = 20

    def _setSamplerate(self, samplerate):
        pass   

    def _setAnalogInputRange(min_voltage, max_voltage):
        pass 

    def _setTriggerSource(self, trigger_source):
        self._trigger_source = trigger_source
        pass

    def _setNumberOfSamples(self, n_samples):
        pass

    def _setInputChannels(self, input_channels):
        pass

    def _singleSweep(self):
        import time        
        import numpy as np        
        if hasattr(self, "_trigger_source"):
            start_time = time.time()
            while not start_time + self.TIMEOUT < time.time():
                if self._trigger_source.is_set():
                    time.sleep(0.01)
                else:
                    break
            else:
                return np.zeros((self._n_samples,))
        time.sleep(self._n_samples/self._samplerate)
        return np.random.uniform(self._min_voltage, self._max_voltage, size=(self._n_samples,))

    def _getData(self):
        raise NotImplementedError

        