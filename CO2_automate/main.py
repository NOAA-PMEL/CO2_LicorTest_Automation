# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 12:31:48 2018

@author: casari
"""

import sys
import os
import serial
import time
import datetime
import pandas as pd
import json
from licor_li820 import *



class Valves:
    def __init__(self,data):
        """ Adding 
            
        
            
        """
        self.valve = data['Valve']
        self.concentration = data['Concentration']
        x = time.strptime(data['Flowtime'],"%H:%M:%S")
        self.flow = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        x = time.strptime(data['Dwelltime'],"%H:%M:%S")
        self.dwell = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        x = time.strptime(data['Venttime'],"%H:%M:%S")
        self.vent = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        

class Automation:
    def  __init__(self,port,filename,jdata):
        self.licor = Licor(port,"LI820",filename)
        self.licor.close()
        self.licor.open()
        self._sys = self.licor.get_system()
        self._create_file(filename)
        
        self.num_repeats = []
        self.gas_time = [None]*8
        self.vent_time = []
        
        self._zero = Valves(jdata['automate']['Zero'])
        self._span = Valves(jdata['automate']['Span'])
        self._valve = []
        
        self._current_gas = '10ppm'
        
        # Dataframe
#        self.df = pd.DataFrame()
        for i in range(0,len(config['automate'])-4):
            name = 'V' + str(i+1)
            self._valve.append(Valves(jdata['automate'][name]))
        return
        

    def zero(self):
        pass
        # Turn data off
#        self.licor.
    def span(self):
        pass
    
    def _create_file(self,filename):
        i = 0
        while(os.path.exists(filename+"%s.json" % i)):
            i += 1
        self.file = open(filename +"%s.json" % i, 'w')
            
        jdata = json.dumps(self._sys,ensure_ascii=False,sort_keys=False,indent=4)
        print(jdata)
        self.file.write(jdata)
        
        return
    
    def _save_data(self):
        jdata = self.df.to_json()
#        print(json.dumps(jdata))
        self.file.write(jdata)
#        print(json.dumps(self.df.to_dict()))
    
    def _timer(self):
        # Read Licor Data
        
        data = self.licor.get_data()
        t = time.strftime('%Y/%m/%d %H:%M:%S')
#        print(type(data))
#        print(data)
        data['time'] = t
        data['gas'] = self._current_gas
        try:
            self.df = self.df.append(data,ignore_index=True)
        except:
#            self.df = pd.DataFrame()
            self.df = data
        self.df
#        print(self.df)
        # Save Licor Data
        pass
    
    def _set_timer(self,seconds):
        pass

if __name__ == '__main__':
    
    

    
    
    ## Load the config file
    
    with open('config.json') as json_data:
        config = json.load(json_data)
        print(config)
#        config = pd.read_json('config.json')
#        print(config)

    ## Setup
    sensor = Automation("COM1","Test",config)
    
    
#    size
    
    for i in range(0,5):
        sensor._timer()
    
    print(sensor.df)
    
    
    
    sensor._save_data()
    sensor.licor.close()
    sensor.file.close()