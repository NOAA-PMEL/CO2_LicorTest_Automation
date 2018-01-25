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
import threading
from operator import itemgetter

import syscontrol
from licor_li820 import *



class Valves:
    def __init__(self,data):
        """ Adding 
            
        
            
        """
        self.valve = int(data['Valve'])
        self.concentration = data['Concentration']
        x = time.strptime(data['Flowtime'],"%H:%M:%S")
        self.flow = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        x = time.strptime(data['Dwelltime'],"%H:%M:%S")
        self.dwell = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        x = time.strptime(data['Venttime'],"%H:%M:%S")
        self.vent = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        
    
class Automation:
    def  __init__(self,port,filename,config):
        self.licor = Licor(port,"LI820",filename)
        self.licor.close()
        self.licor.open()
        self._sys = self.licor.get_system()
        
        self._savefile = os.path.join(config['automate']['Path'],filename)
        self.num_repeats = int(config['automate']['NumCycles'])
        
#        self._create_file(filename)
        self._create_file(self._savefile)
        
        
        self.gas_time = [None]*8
        self.vent_time = []
        
        self._zero_valve = []#Valves(jdata['automate']['Zero'])
        self._span_valve = []#Valves(jdata['automate']['Span'])
        self._valve = []
        
        self._current_gas = '5ppm'
        
        # Dataframe
#        for i in range(0,len(config['automate']['Gases'])):
#            name = 'V' + str(i+1)
#            self._valve.append(Valves(jdata['automate']['Gases'][name]))
#        return
#    
#        self._zero = config['automate']['Gases']['Zero']
#        self._span = config['automate']['Gases']['Span']
#        self._current_valve = []
        i=0
#        for c in config['automate']['Gases']:
        for c in sorted(config['automate']['Gases'].values(),key=itemgetter('Valve')):
#            self._valve.append(Valves(config['automate']['Gases'][c]))
            self._valve.append(Valves(c))
            
        self._zero_valve = config['automate']['Gases']['Zero']
        self._span_valve = config['automate']['Gases']['Span']

    def zero(self):
        pass
#        # Turn data off
##        self.licor.
#    def span(self):
#        pass
#    
#    def valve(self,valve):
#        pass
    
    def _create_file(self,filename):
        i = 0
        while(os.path.exists(filename+"%s.json" % i)):
            i += 1
        self.file = open(filename +"%s.json" % i, 'w')
        
        temp = {'Licor Settings':self._sys}
#        jdata = json.dumps(self._sys,ensure_ascii=False,sort_keys=False,indent=4)
        jdata = json.dumps(temp,ensure_ascii=False,sort_keys=False,indent=4)
        print(jdata)
        self.file.write(jdata)
        
        return
    
    def _save_data(self):
        self.file.write(',\n')
        jdata = self.df.to_json()
        # @todo Replace Gases with Gas X or Valve x
        temp = '{\"Gases\":'  # '{\"Gas %s\":' % self._current_valve.valve
        jdata = temp + jdata + '}'
        self.file.write(jdata)
        
        # @todo Add pretty print?

    
    def _timer(self):
        # Read Licor Data
        data = self.licor.get_data()
        
        t = time.strftime('%Y/%m/%d %H:%M:%S')

        data['time'] = t
        data['gas'] = self._current_gas
        try:
            self.df = self.df.append(data,ignore_index=True)
        except:
            self.df = data
        self.df
        # Save Licor Data
        pass
    
    def _set_timer(self,seconds):
        pass

if __name__ == '__main__':
    
    ## Load the config file
    with open('config.json') as json_data:
        config = json.load(json_data)
        print(config)

    ## Setup
    sensor = Automation("COM1","Test",config)
    
    ## Zero
    ## Open the Zero Valve & Valve 9 and wait, then set span in Licor
    
    ## Span
    ## Open the Span Valve & Valve 9 and wait, then set span in Licor
    
##    size
#    
    for i in range(0,5):
        sensor._timer()
    
#    print(sensor.df)
    
    
    
    sensor._save_data()
    sensor.licor.close()
    sensor.file.close()