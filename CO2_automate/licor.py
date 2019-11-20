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

class Licor:
    def __init__(self,port,model, filename):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = 9600
        self.ser.stopbits = 1
        self.ser.timeout = 1 #2.5
        self.filename = filename
        self.model = model
        self._data_streaming = False
        return
            
    def open(self):
        # print("Open Serial Port")
        try:
            self.ser.open()
        except:
            self.ser.close()
            raise ValueError
        
        self.ser.flush()

        # print("Commanding ack 1")
        self._command_ack()

        # print("Stop Data")
        self._stop_data()
        self.ser.flush()

        # print("Commanding ack 2")
        self._command_ack()

        # print("Set Outputs")
        self._set_outputs()
        self.ser.flush()

        print("Starting Data Stream")
        self.ser.flush()
        ack = False
        while ack == False:
            ack = self._start_data(rate=0.5) 
            self.ser.flush()
        
        return
    
    def close(self):
        self.ser.close()
        return
    
    def set_zero(self):
        # Stop the data stream and clear the buffer 
        self._stop_data()
        time.sleep(0.5)
        
        # Create the date string and xml grammar for the command 
        date  = time.strftime("%Y-%m-%d",time.gmtime())
        xmlstr = "<CAL><DATE>%s</DATE><CO2ZERO>TRUE</CO2ZERO></CAL>"%date

        if self.model == "LI820":
            xmlstr = "<LI820>" + xmlstr + "</LI820>"
        elif self.model == "LI830":
            xmlstr = "<LI830>" + xmlstr + "</LI830>"

        # Flush the buffer and write
        self.ser.flush()
        self.ser.write(xmlstr.encode())
        
        # Wait for the response
        time.sleep(1.0)

        ## Check for ACK
        self._check_ack()
        self.ser.flush()
        
        valid = False
        print("Zero: Wait for Licor Response ",end="")
        for i in range(0,60):
            print(".",end="")
            line = self.ser.readline().decode()
#            print(line)
            if(len(line)>0):
                if(line.find("error")>-1):
                        valid = False
                elif(len(line)==0):
                    valid = False
                else:
                    valid = True
                    break
        
        print("\nZero Complete\n")
                    
        assert(valid == True)
        return
    
    def set_span(self,span,ppm):
        # Stop the data stream and clear the buffer 
        self._stop_data()
        time.sleep(0.5)
        
        # Create the date string and xml grammar for the command 
        date  = time.strftime("%Y-%m-%d",time.gmtime())
        spanstr = []
        if(span == 1):
            spanstr = "CO2SPAN>"
        elif(span==2):
            spanstr = "CO2SPAN2>"
            
        xmlstr = "<CAL><DATE>" + date + "</DATE><CO2SPAN>%d</CO2SPAN></CAL>" % int(ppm)

        if self.model == "LI820":
            xmlstr = "<LI820>" + xmlstr + "</LI820>"
        elif self.model == "LI830":
            xmlstr = "<LI830>" + xmlstr + "</LI830>"
        # Flush the buffer and write
        self.ser.flush()
        self.ser.write(xmlstr.encode())
        
        # Wait for the response
        time.sleep(1.0)

        ## Check for ACK
        self._check_ack()
        self.ser.flush()
        
        valid = False
        print("Span: Wait for Licor Response ",end="")
        for i in range(0,60):
            print(".",end="")
            line = self.ser.readline().decode()

            if(len(line)>0):
                if(line.find("error")>-1):
                        valid = False
                elif(len(line)==0):
                    valid = False
                else:
                    valid = True
                    break

        
        print("\nSpan Complete\n")          
            
                    
        assert(valid == True)
        return
                
            
        
    def get_system(self):
        
        # Turn data off
        self._stop_data()

        ## Query the Licor
        if self.model == "LI820":
            sendstr = "<LI820>?</LI820>"
        elif self.model == "LI830":
            sendstr = "<LI830>?</LI830>\r\n"

        self.ser.write(sendstr.encode())

        
        # Read data
        data = self.ser.readline()
        data = data.decode()
        
        # Convert data from XML to JSON
        # Save Data to file
        data_xml = ET.XML(data)
        return etree_to_dict(data_xml)
    
    def get_data(self):
        if self._data_streaming == False:
            ack = False
            while ack == False:
                ack = self._start_data(rate=0.5) 
                self.ser.flush()

        
        
        data = self.ser.readline().decode()
        if data:
            return self._convert_xmldata_to_dataframe(data)
        else:
            return None
        # xml2df = XML2DataFrame(data)
        # return xml2df.process_data()

    def _convert_xmldata_to_dataframe(self, xmldata):
        
        if self.model == 'LI830':
            xroot = ET.XML(xmldata)
            # print(xmldata)
            try:
                s_data = xroot.find('data')
                s_raw = s_data.find('raw')
                data = {
                    'celltemp':[float((s_data.find('celltemp')).text)],
                    'cellpres':[float((s_data.find('cellpres')).text)],
                    'co2':[float((s_data.find('co2')).text)],
                    'co2abs':[float((s_data.find('co2abs')).text)],
                    'ivolt':[float((s_data.find('ivolt')).text)],
                    'raw_co2':[float((s_raw.find('co2')).text)],
                    'raw_co2abs':[float((s_raw.find('co2ref')).text)]
                }
            except:
                print('Invalid XML Data')
                data = {}
        df = pd.DataFrame.from_dict(data)

        return df    

    def _start_data(self, rate = 1):

        sendstr = "<cfg><outrate>" + str(rate) + "</outrate></cfg>\r\n"
        if self.model == "LI820":
            sendstr = "<li820><cfg><outrate>" + str(rate) + "</outrate></cfg></li820>\r\n"
        elif self.model == "LI830":
            sendstr = "<li830><cfg><outrate>" + str(rate) + "</outrate></cfg></li830>\r\n"
        # print(sendstr)
        ack = False
        ack = self._check_ack()
        for i in range(0,3):
            self.ser.flush()
            if rate == 0:
                reps = 5
            else:
                reps = 1
            for i in range(0,reps):
                self.ser.write(sendstr.encode())

            if self._check_ack(10):
                ack = True
                break
        
        if(rate > 0.0):
            self._data_streaming = True
            # assert(self._data_streaming == True)
        return ack
    
    def _stop_data(self):
        ack = False
        idx = 0
        while ack == False:
            idx += 1
            print("Stop Attempt: " + str(idx))
            ack = self._start_data(rate=0) 
            time.sleep(0.25)
            self.ser.flush()
            
        print("data stopped")
        
    
    def _check_streaming(self):
        line = self.ser.readline()
        assert(len(line) > 0)
        return
    
    def _check_ack(self,numlines=2):
        valid = False
        for i in range(0,numlines):
            line = self.ser.readline()
            
            line = line.decode()
            line = line.strip("\r\n")
            line = line.lower()
            # print(line)
            valid = False
            if self.model == "LI820":
                if(line == "<li820><ack>true</ack></li820>"):
                    valid = True
            elif self.model == "LI830":
                if line.find("<li830><ack>true</ack></li830>") > -1:
                    valid = True
            if valid:
                break;
        self.ser.flush()
        return valid

    def _command_ack(self):
        if self.model == "LI820":
            sendstr = "<li820>ack</li820>"
        elif self.model == "LI830":
            sendstr = "<li830>ack</li830>"
        
        ack = False
        while False == ack:
            self.ser.flush()
            self.ser.write(sendstr.encode())
            if self._check_ack():
                ack = True
        
        
        
    def _set_outputs(self):
        if self.model == "LI820":
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
            strip = "<strip>False</strip>"
            sendstr = startstr + co2 + co2abs + h2o + h2oabs + h2odew + cellt + cellp + ivolt + raw + echo + strip + endstr
        elif self.model == "LI830":
            # sendstr = "<li830><cfg><outrate>0</outrate></cfg><rs232><co2>true</co2><co2abs>true</co2abs><h2o>false</h2o><h2odewpoint>false</h2odewpoint><h2oabs>false</h2oabs><celltemp>true</celltemp><cellpres>true</cellpres><ivolt>true</ivolt><echo>false</echo><strip>false</strip><flowrate>false</flowrate><raw><co2>False</co2><co2ref>False</co2ref></rs232></li830>"
            sendstr = "<li830><cfg><outrate>0</outrate></cfg><rs232><co2>true</co2><co2abs>true</co2abs><h2o>false</h2o><h2odewpoint>false</h2odewpoint><h2oabs>false</h2oabs><celltemp>true</celltemp><cellpres>true</cellpres><ivolt>true</ivolt><echo>false</echo><strip>false</strip><flowrate>false</flowrate></rs232></li830>\r\n"
        self.ser.flush()
        print("Set the output")
        ack = False
        while ack == False:
            # self._command_ack()

            self.ser.flush()
            self.ser.write(sendstr.encode())
            # Wait for the response
            
            ack = self._check_ack()
            print("Ack is: " + str(ack))


        
        
        
if __name__ == '__main__':

    L = Licor("COM12","LI830","Test")
    L.open()
    print("Starting")
    time.sleep(1)
    for i in range(0,20):
        print(i)
        print(L.get_data())


    L.close()


    # try:
    #     L = Licor("COM1","LI830","Test")
    #     L.open()
    #     print("Starting")
    #     time.sleep(1)
    #     for i in range(0,20):
    #         print(i)
    #         print(L.get_data())
    # except Exception as e:
    #     print("Failure")
    #     print(e)