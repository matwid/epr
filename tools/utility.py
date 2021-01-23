import time
import os
import pickle

# Enthought library imports
from traits.api import Float, HasTraits, HasPrivateTraits, Str, Tuple, File, Button
from traitsui.api import Handler, View, Item, OKButton, CancelButton
from traitsui.file_dialog import open_file, save_file


import logging

from tools.data_toolbox import writeDictToFile

import threading

def timestamp():
    """Returns the current time as a human readable string."""
    return time.strftime('%y-%m-%d_%Hh%Mm%S', time.localtime())

class Singleton(type):
    """
    Singleton using metaclass.
    
    Usage:
    
    class Myclass( MyBaseClass )
        __metaclass__ = Singleton
    
    Taken from stackoverflow.com.
    http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]



class History(object):
    """History of length 'length'."""
    def __init__(self, length):
        self.length = length
        self.items = [ ]
        self.i = 0

    def get(self):
        return self.items[self.i]

    def back(self):
        if self.i != 0:
            self.i = self.i - 1
        return self.items[self.i]

    def forward(self):
        if self.i != len(self.items) - 1:
            self.i = self.i + 1
        return self.items[self.i]
    def setposition(self,position):        
        if position < len(self.items):
            self.i = position
        else:
            pass
        return self.items[self.i]


    def put(self, item):
        while self.i < len(self.items) - 1:
            self.items.pop()
        if self.i == self.length - 1:
            self.items.pop(0)
        self.items.append(item)
        self.i = len(self.items) - 1

    def setlength(self, length):
        while len(self.items) > length:
            self.items.pop(0)
            self.i = self.i - 1
        self.length = length


class StoppableThread( threading.Thread ):
    """
    A thread that can be stopped.
    
    Parameters:
        target:    callable that will be execute by the thread
        name:      string that will be used as a name for the thread
    
    Methods:
        stop():    stop the thread
        
    Use threading.currentThread().stop_request.isSet()
    or threading.currentThread().stop_request.wait([timeout])
    in your target callable to react to a stop request.
    """
    
    def __init__(self, target=None, name=None):
        threading.Thread.__init__(self, target=target, name=name)
        self.stop_request = threading.Event()
        
    def stop(self, timeout=10.):
        name = str(self)
        logging.getLogger().debug('attempt to stop thread '+name)
        if threading.currentThread() is self:
            logging.getLogger().debug('Thread '+name+' attempted to stop itself. Ignoring stop request...')
            return
        elif not self.is_alive():
            logging.getLogger().debug('Thread '+name+' is not running. Continuing...')
            return
        self.stop_request.set()
        self.join(timeout)
        if self.is_alive():
            logging.getLogger().warning('Thread '+name+' failed to join after '+str(timeout)+' s. Continuing anyway...')


from traits.api import HasPrivateTraits, SingletonHasPrivateTraits

class DialogBox( HasPrivateTraits ):
    """Dialog box for showing a message."""
    message = Str
    
class FileDialogBox( SingletonHasPrivateTraits ):
    """Dialog box for selection of a filename string."""
    filename = File

def warning( message='', buttons=[OKButton, CancelButton] ):
    """
    Displays 'message' in a dialog box and returns True or False
    if 'OK' respectively 'Cancel' button pressed.
    """    
    dialog_box = DialogBox( message=message )
    ui = dialog_box.edit_traits(view=View(Item('message', show_label=False, style='readonly'),
                                          buttons=buttons,
                                          width=400, height=150,
                                          kind='modal'
                                          )
                                )
    return ui.result


def save_file(title=''):
    """
    Displays a dialog box that lets the user select a file name.
    Returns None if 'Cancel' button is pressed or overwriting
    an existing file is canceled.
    
    The title of the window is set to 'title'.
    """    
    dialog_box = FileDialogBox()

    ui = dialog_box.edit_traits(View(Item('filename'),
                                     buttons = [OKButton, CancelButton],
                                     width=400, height=150,
                                     kind='modal',
                                     title=title
                                     )
                                )
    if ui.result:
        if not os.access(dialog_box.filename, os.F_OK) or warning('File exists. Overwrite?'):
            return dialog_box.filename
        else:
            return

class GetSetItemsMixin( HasTraits ):
    """
    Provides save, load, save figure methods. Useful with HasTraits models.
    Data is stored in a dictionary with keys that are strings and identical to
    class attribute names. To save, pass a list of strings that denote attribute names.
    Load methods accept a filename. The dictionary is read from file and attributes
    on the class are set (if necessary created) according to the dictionary content. 
    """

    filename = File()
    
    save_button = Button(label='save', show_label=False)
    load_button = Button(label='load', show_label=False)

    get_set_items = [] # Put class members that will be saved upon calling 'save' here.
    # BIG FAT WARNING: do not include List() traits here. This will cause inclusion of the entire class definition  during pickling
    # and will result in completely uncontrolled behavior. Normal [] lists are OK.

    def set_items(self, d):
        # In order to set items in the order in which they appear
        # in the get_set_items, we first iterate through the get_set_items
        # and check whether there are corresponding values in the dictionary.
        for key in self.get_set_items:
            try:
                if key in d:
                    val = d[key]
                    attr = getattr(self, key)
                    if isinstance(val,dict) and isinstance(attr, GetSetItemsMixin): # iterate to the instance
                        attr.set_items(val)
                    else:
                        setattr(self, key, val)
            except:
                logging.getLogger().warning("failed to set item '"+key+"'")

    def get_items(self, keys=None):
        if keys is None:
            keys = self.get_set_items
        d = {}
        for key in keys:
            attr = getattr(self, key)
            if isinstance(attr, GetSetItemsMixin): # iterate to the instance
                d[key] = attr.get_items()
            else:
                d[key] = attr
        return d

    def save(self, filename):
        """detects the format of the savefile and saves it according to the file-ending. .txt and .asc result in an ascii sav,
        .pyd in a pickled python save with mode='asc' and .pys in a pickled python file with mode='bin'"""
        if not filename:
            raise IOError('Empty filename. Specify a filename and try again!')
        writeDictToFile(self.get_items(),filename)

         
    def load(self, filename):
        if filename == '':
            raise IOError('Empty filename. Specify a filename and try again!')
        if os.access(filename, os.F_OK):
            logging.getLogger().debug('attempting to restore state of '+self.__str__()+' from '+filename+'...')
            try:
                logging.getLogger().debug('trying binary mode...')  
                self.set_items(pickle.load(open(filename,'rb')))
            except:
                try:
                    logging.getLogger().debug('trying text mode...')  
                    self.set_items(pickle.load(open(filename,'r')))
                except:
                    try:
                        logging.getLogger().debug('trying unicode text mode...')  
                        self.set_items(pickle.load(open(filename,'rU')))
                    except:
                        logging.getLogger().debug('failed to restore state of '+self.__str__()+'.')  
                        raise IOError('Load failed.')
            logging.getLogger().debug('state of '+self.__str__()+' restored.')
        else:
            raise IOError('File does not exist.')
        
    ##################################################################################################################
    # new Save Button function, basiclly all in one Function. Path gets set after pressing button.
    ##################################################################################################################
    def _save_button_fired(self, dict):
        self.filename =save_file()
        if os.access(self.filename, os.F_OK)
        try:
            try:        # if there is a doc string put it up front
        datastring= '#__doc__\n'+dict['__doc__']+'\n'
        del dict['__doc__']
        except:
        datastring=''
        measuerd_data_array =[[],[],[]]
        j=0
        for key, value in dict.items():
            datastring+= '#'+key+'\n' # header for each key
            #blub(value)
            if hasattr(value,'__iter__'): # array? 
                if value!=[]:
                    if hasattr(value[0],'__iter__'): # 2d array?
        
                        #2d array
                        for i in range(value.shape[0]):
                            for j in range(value.shape[1]):
                                datastring+=(str(value[i,j])+', ')
                                if j==value.shape[1]-1:
                                    datastring+='\n'
                                    
                    else: 
                        #1d array
                        try:
                            n=value.shape[0]
                        except:
                            n=len(value)
                        
                        if j <= 2:
                            for i in range(n):
                                measuerd_data_array[j].append(value[i])
                        j+=1
                else: 
                    datastring=datastring+' '+'/n'
        
            else:
                # value no array
                datastring=datastring+str(value)+'\n'  

        array_data = ''
        measuerd_data_array= np.transpose(measuerd_data_array)
        for i in range(len(measuerd_data_array)):
            array_data += (str(measuerd_data_array[i][0])+'\t'+str(measuerd_data_array[i][1])+'\t'+str(measuerd_data_array[i][2])+'\n')
        datastring=datastring +'\n'+ array_data )
            stringToFile(d,filename)
            
        try:
            f=open(path,'w')
            try:
                f.write(datastring)
            finally:
                f.close()
        except IOError:
            print( 'Error exporting data')
            return False
        return True


    ##################################################################################################################
    ##################################################################################################################


    def _load_button_fired(self):
        try:
            self.load(self.filename)
        except IOError as err:
            warning(err.message, buttons=[OKButton])

    def copy_items(self, keys):
        d = {}
        for key in keys:
            item = getattr(self, key)
            if hasattr(item,'copy'):
                d[key] = item.copy()
            else:
                d[key] = item
        return d


class GetSettableHistory(History,GetSetItemsMixin):
    """
    Implements a history that can be pickled and unpickled
    in a generic way using GetSetItems. When this class is used,
    the data attached to the history is saved instead of
    the history object, which otherwise would require the definition
    of the history class to be present when unpickling the file.
    """
    get_set_items=['items','length','i']


if __name__ is '__main__':
    pass
