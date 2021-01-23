import os


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







def _save_button_fired(self):
    self.filename = save_file()
    if os.access(self.filename, os.F_OK):
        if not warning('File exists. Overwrite?'):
            return
    try:
        self.save(self.filename)
    except IOError as err:
        warning(err.message, buttons=[OKButton])


def save(self, filename):
        if not filename:
            raise IOError('Empty filename. Specify a filename and try again!')
        writeDictToFile(self.get_items(),filename)


def writeDictToFile(dict, filename):
        d=dictToAscii(dict)
        stringToFile(d,filename)
    
def dictToAscii(dict, keys=None):
    #Converts a dictionary or parts of it to a string
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
    datastring=datastring +'\n'+ array_data 
    return datastring
    

def stringToFile(datastring, path):
    """writes datastring to file"""
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


    ################################################################################################################################################
    ################################################################################################################################################
    ################################################################################################################################################

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


    ################################################################################################################################################
    ################################################################################################################################################
    ################################################################################################################################################            