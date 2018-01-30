# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 12:31:48 2018

@author: casari
"""

import sys
import os
import time
import datetime
import pandas as pd
import json
from operator import itemgetter

import syscontrol
from licor_li820 import *
from serialports import *



class Valves:
    def __init__(self,data):
        """ Adding 
            
        
            
        """
        self.valve = int(data['Valve'])-1
        self.concentration = data['Concentration']
        x = time.strptime(data['Flowtime'],"%H:%M:%S")
        self.flow = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        x = time.strptime(data['Dwelltime'],"%H:%M:%S")
        self.dwell = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        try:
            x = time.strptime(data['Prep'],"%H:%M:%S")
            self.prep = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
            x = time.strptime(data['Cal'],"%H:%M:%S")
            self.cal = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        except:
            pass
class Automation:
    def  __init__(self,port,filename,config):
        ## Create the Licor sensor object, open the port and get the system configurations
        self.licor = Licor(port,"LI820",filename)
        
        self.licor.ser.close()
        self.licor.close()
        self.licor.open()
#        self._sys = self.licor.get_system()
        
        ## Populate variables from the config file values
        self._savefile = os.path.join(config['automate']['Path'],filename)
        self.num_repeats = int(config['automate']['NumCycles'])
        x = time.strptime(config['automate']['CycleDelay'],"%H:%M:%S")
        self._cycledelay = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        ## Create the test save file
        self._create_file(self._savefile)
        
        ## Create the valve objects
        self._valve = []
        for c in sorted(config['automate']['Gases'].values(),key=itemgetter('Valve')):
            self._valve.append(Valves(c))
            
        self._zero_valve = Valves(config['automate']['Gases']['Zero'])
        self._span_valve = Valves(config['automate']['Gases']['Span'])
        
        ## Create the 
        self._current_gas = '5ppm'
        
        ## Create a variable for the vale to run
        self._current_valve = self._zero_valve
        
        ## Run the Zero
        self.zero()
        
        ## Run the Span
        self.span()
        
        ## Get the system info
        self.sysinfo()
        
        return

    def sysinfo(self):
        self._sys = self.licor.get_system()
        temp = {'Licor Settings':self._sys}
        jdata = json.dumps(temp,ensure_ascii=False,sort_keys=False,indent=4)
        print(jdata)
        self.file.write(jdata)
        return
    
    def stop(self):
        self._close_all_valves()
        self.licor.close()
        self.file.close()
        return
    
    def run(self):
        ## Run through the list of valves and operate them
        for i in range(self.num_repeats):
            self.licor._start_data()
            time.sleep(1)
            self.licor.ser.flush()
            print("\n******** Run #%d********" % (i+1))
            for valve in self._valve:
                if( (valve.valve != self._zero_valve.valve) and (valve.valve != self._span_valve.valve)):
                    
                    ## Set the valve
                    self._current_valve = valve
                    
                    ## Start running the collection
                    self._run_valve(valve)
                    
                    ## Save the data
                    self._save_data()
                    
            ## Read the values for the zero gas
            self._current_valve = self._zero_valve
            self._run_valve(self._zero_valve)
            self._save_data()
            
            ## Read the values for the span gas
            self._current_valve = self._span_valve
            self._run_valve(self._span_valve)
            self._save_data()
            
            ## Stop Licor Streaming
            self.licor._stop_data()
            
            ## Make sure all valves are closed
            self._close_all_valves()
            
            ## Delay if needed
            if(self.num_repeats > 0):
                dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=self._cycledelay)
                while(datetime.datetime.utcnow() < dt):
                    time.sleep(1)
           
        
        return
    
    def _run_valve(self,valve):
#        print("\n")
        # Set the valve
        syscontrol.OpenValve(valve.valve)
        # while time < flow time Read the data every second
        dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=valve.flow)
        while(datetime.datetime.utcnow() < dt):
            print('.',end="")
            self._get_data()
        
        print("\n",end="")
        # Close the valve
        syscontrol.CloseValve(valve.valve)
        # while time < dwell time Read the data every second
        dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=valve.dwell)
        while(datetime.datetime.utcnow() < dt):
            print('.',end="")
            self._get_data()
        print("")
        return
            
    def zero(self):
        print("\nZero: Start Flow ",end="")
        syscontrol.OpenValve(self._zero_valve.valve)
        dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=self._zero_valve.prep)
        while(datetime.datetime.utcnow() < dt):
            time.sleep(1)
            print('.',end="")
        
        print("\nZerp: Stop Flow ", end="")
        syscontrol.CloseValve(self._zero_valve.valve)
        dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=self._zero_valve.cal)
        while(datetime.datetime.utcnow() < dt):
            time.sleep(1)
            print('.',end="")
        print("\nZero: Set Licor");
        self.licor.set_zero()
        return
        
    def span(self):
        print("\nSpan: Start Flow ",end="")
        syscontrol.OpenValve(self._span_valve.valve)
        dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=self._span_valve.prep)
        while(datetime.datetime.utcnow() < dt):
            time.sleep(1)
            print('.',end="")
        
        print("\nSpan: Stop Flow ", end="")
        syscontrol.CloseValve(self._span_valve.valve)
        dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=self._span_valve.cal)
        while(datetime.datetime.utcnow() < dt):
            time.sleep(1)
            print('.',end="")
        print("\nSpan: Set Licor");
        self.licor.set_span(1,self._span_valve.concentration)

        return
    def _close_all_valves(self):
        syscontrol.CloseValve(0)
        syscontrol.CloseValve(1)
        syscontrol.CloseValve(2)
        syscontrol.CloseValve(3)
        syscontrol.CloseValve(4)
        syscontrol.CloseValve(5)
        syscontrol.CloseValve(6)
        syscontrol.CloseValve(7)
        syscontrol.CloseValve(8)
        return
    
    def _create_file(self,filename):
        i = 0
        while(os.path.exists(filename+"%s.json" % i)):
            i += 1
        self.file = open(filename +"%s.json" % i, 'w')
        
        return
    
    def _save_data(self):
        self.file.write(',\n')
        print(self.df)
        jdata = self.df.to_json()
        temp = '{\"Gas %s\":' % self._current_valve.valve
        jdata = temp + jdata + '}'
        self.file.write(jdata)
        # @todo Add pretty print?

        del(self.df)
        return
    
    def _get_data(self):
        self.licor.ser.flush()
        # Read Licor Data
        data = self.licor.get_data()
        
        
        ## Add the time to the data
        t = time.strftime('%Y/%m/%d %H:%M:%S')
        data['time'] = t
        
        ## Add the current gas to the data
        data['gas'] = self._current_valve.concentration
        
        
        try:
            self.df = self.df.append(data,ignore_index=True)
        except:
            self.df = data
        
        return
    
    def _set_timer(self,seconds):
        pass

if __name__ == '__main__':
    
    print("##### Valve Automation Program #####")
          
    ## Grab the file path and point towards the config file
    path = os.path.dirname(sys.argv[0])
#    print(path)
    if(path[path.rfind('/')+1:]!="CO2_automate") :
        path = os.path.join(path,'CO2_automate')
#    print(path)
    configfile = os.path.join(path,'config.json')\
    
    ## Get the Serial Port
    if(len(sys.argv) == 1):
        ports = Find_Serial()
        i=0
        print("Select Licor Serial port from list:")
        for port in ports:
            print("%s - " % (i+1) + port)
            i += 1
        pval = input("Licor Serial Port = ")
        pval = int(pval) - 1
        licorPort = ports[pval]
    else:
        licorPort = sys.argv[1]
    print(licorPort + " selected")
    
    ## Run the primary program
    try:
        ## Load the config file
        print("Loading Config File")
        with open(configfile) as json_data:
            config = json.load(json_data)
    
        ## Setup
        print("Starting Test")
        sensor = Automation(licorPort,"Test",config)
        
        ## Run the test
        sensor.run()
    
    except Exception as e:
        print(e)

    ## Close down
    try:
        sensor.stop()
    except:
        pass
    
    
    
    
