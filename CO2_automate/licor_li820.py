# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 12:37:25 2018

@author: casari
"""

import serial
import time
import xml.etree.ElementTree as ET
import pandas as pd


from collections import defaultdict

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

class XML2DataFrame:

    def __init__(self, xml_data):
        print(xml_data)
        self.root = ET.XML(xml_data)

    def parse_root(self, root):
        return [self.parse_element(child) for child in iter(root)]

    def parse_element(self, element, parsed=None):
        if parsed is None:
            parsed = dict()
        for key in element.keys():
            parsed[key] = element.attrib.get(key)
        if element.text:
            parsed[element.tag] = element.text
        for child in list(element):
            self.parse_element(child, parsed)
        return parsed

    def process_data(self):
        structure_data = self.parse_root(self.root)
        return pd.DataFrame(structure_data)

class Licor:
    def __init__(self,port,model, filename):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = 9600
        self.ser.stopbits = 1
        self.ser.timeout = 2.5
        self.filename = filename
        self.model = model
#        self.ss = "<" + self.model + ">"
#        self.ee = "</" + self.model + ">"
        
#        self.f = open(filename,'w+');
            
    def open(self):
        self.ser.open()
        self._stop_data()
        self.ser.flush()
        self._set_outputs()
        self.ser.flush()
    
    def close(self):
        self.ser.close()
        
    def set_zero(self):
        # Stop the data stream and clear the buffer 
        self._stop_data()
        time.sleep(0.5)
        
        # Create the date string and xml grammar for the command 
        date = time.strftime("%Y-%m-%d",time.gmtime())
        xmlstr = "<li820><cal><date>" + date + "</date><co2zero>true</co2zero></cal></li820>"
        
        # Flush the buffer and write
        self.ser.flush()
        self.ser.write(xmlstr.encode())
        
        # Wait for the response
#        time.sleep(1.0)
#        line = self.ser.readline()
#        self._check_ack(line.decode())
        self._check_ack()
        
        
    def set_span(self,span,ppm):
        
        # Stop the data stream and clear the buffer 
        self._stop_data()
        time.sleep(0.5)
        
        # Create the date string and xml grammar for the command 
        date  = time.strftime("%Y-%m-%d",time.gmtime())
        spanstr = []
        if(span == 1):
            spanstr = "co2span>"
        elif(span==2):
            spanstr = "co2span2>"
            
        xmlstr = "<li820><cal><" + spanstr + date + "</" + spanstr + "<co2zero>" + str(ppm) + "</co2zero></cal></li820>"
        
        # Flush the buffer and write
        self.ser.flush()
        self.ser.write(xmlstr.encode())
        
        # Wait for the response
#        time.sleep(1.0)
#        line = self.ser.readline()
#        self._check_ack(line.decode())
        self._check_ack()
        
    def get_system(self):
        
        # Turn data off
        self._stop_data()
#        self.ser.flush()
#        time.sleep(2.0)
        # Read Data from Licor
#        self.ser.flush()
        
        sendstr = "<li820>?</li820>"
        self.ser.write(sendstr.encode())

        
        # Read data
        
        data = self.ser.readline()
        data = data.decode()
        
        # Convert data from XML to JSON
        # Save Data to file
        # @todo Add save to file
#        xml2df = XML2DataFrame(data)
#        xml_dataframe = xml2df.process_data()
#        return xml_dataframe
        data_xml = ET.XML(data)
        return etree_to_dict(data_xml)
    
    def _start_data(self, rate = 1.0):
        sendstr = "<li820><cfg><outrate>" + str(rate) + "</outrate></cfg></li820>"
#        print(sendstr)
        self.ser.write(sendstr.encode())
#        time.sleep(0.5)
#        line = self.ser.readline()
#        self._check_ack(line.decode())
        self._check_ack()
    def _stop_data(self):
        sendstr = "<li820><cfg><outrate>0.0</outrate></cfg></li820>"
        self.ser.write(sendstr.encode())
        self._check_ack()
        
    def _check_ack(self):
#        time.sleep(1.0)
        line = self.ser.readline()
        line = line.decode()
        line = line.strip("\r\n")
        assert(line == "<li820><ack>true</ack></li820>")
        self.ser.flush()
        
        
    def _set_outputs(self):
        startstr = "<li820><rs232>"
        endstr = "</rs232></li820>"
        co2 = "<co2>True</co2>"
        co2abs = "<co2abs>True</co2abs>"
        h2o = "<h2o>False</h2o>"
        h2oabs = "<h2oabs>False</h2oabs>"
        h2odew = "<h2odewpoint>False</h2odewpoint>"
        cellt = "<celltemp>True</celltemp>"
        cellp = "<cellpres>True</cellpres>"
        ivolt = "<ivolt>True</ivolt>"
        raw = "<raw>True</raw>"
        echo = "<echo>False</echo>"
        strip = "<strip>True</strip>"
        
        # Create the output string
        sendstr = startstr + co2 + co2abs + h2o + h2oabs + h2odew + cellt + cellp + ivolt + raw + echo + strip + endstr
        
        # Stop the data stream
        self._stop_data()
        time.sleep(1)
        
        # Flush the buffer and write
        self.ser.flush()
        self.ser.write(sendstr.encode())
        
        # Wait for the response
#        time.sleep(0.5)
#        line = self.ser.readline()
#        self._check_ack(line.decode())
        self._check_ack()
        
        
        
if __name__ == '__main__':
    L = Licor("COM1","LI820","Test")
    try:
        L.open()
    #        L.set_zero()
    #        L.set_span(1,100)
    #        L.get_system()
#        L._set_outputs()
        print(L.get_system())
#        L._start_data()
    except Exception as e:
        print("Exception\n")
        print(e)
    
    L.close()