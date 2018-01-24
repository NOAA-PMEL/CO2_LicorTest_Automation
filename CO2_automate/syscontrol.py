# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 10:11:02 2017
Modified Tue Nov 7 16:23:00 2017
@author: casari, turpin
"""

import time
import u3


class VM2000():

    def __init__(self):

        
        self.d = u3.U3()
        self.d.getCalibrationData()
        
        FIOAnalogChans = 0
        EIOAnalogChans = 0
        fios = FIOAnalogChans & 0xFF  
        eios = EIOAnalogChans & 0xFF  
        self.d.configIO(FIOAnalog=fios, EIOAnalog=eios)
        
        self.d.getFeedback(u3.PortDirWrite(Direction=[0, 0, 0], WriteMask=[0, 0, 15]))
        print("Before Feedback")
        #Pin 0 (FIO0) Hold low to select Valves 0-15 on the Valve Master 2000 Board
        self.d.getFeedback(u3.BitStateWrite(IONumber=8, State = 0))
        #Pin 1 (FIO1) Hold low to enable output
        self.d.getFeedback(u3.BitStateWrite(IONumber=9, State = 0))
        #Pin 2 (FIO2) Set Low to disable H-Bridge Drivers Port A (Open Valve)
        self.d.getFeedback(u3.BitStateWrite(IONumber=10, State = 0))
        #Pin 3 (FIO3) Set Low to disable H-Bridge Drivers Port B (Close Valve)
        self.d.getFeedback(u3.BitStateWrite(IONumber=11, State = 0))
        self.d.getFeedback(u3.BitStateWrite(IONumber=12, State = 0))
        self.d.getFeedback(u3.BitStateWrite(IONumber=13, State = 0))
        self.d.getFeedback(u3.BitStateWrite(IONumber=14, State = 0))
        self.d.getFeedback(u3.BitStateWrite(IONumber=15, State = 0))
        
        print("After Feedback")



    def VMCloseValve(self, valve):
    
        print("Close: " + str(valve))
        #Pass Valve Number to be addressed.
        self.ValveAddress(valve)
        #Pulse In2 for addressed Valve
        self.d.getFeedback(u3.BitStateWrite(IONumber=11, State = 1))
        #50ms hold 
        time.sleep(0.05)
        #Pulse In1 to reset Valve
        self.d.getFeedback(u3.BitStateWrite(IONumber=11, State = 0))
        
    def VMOpenValve(self, valve):
        print("Open: " + str(valve))
        #Pass Valve Number to be addressed.
        self.ValveAddress(valve)
        #Pulse In2 for addressed Valve
        self.d.getFeedback(u3.BitStateWrite(IONumber=10, State = 1))
        #50ms hold 
        time.sleep(0.05)
        #Pulse In1 to reset Valve
        self.d.getFeedback(u3.BitStateWrite(IONumber=10, State = 0))
        
    def ValveAddress(self, valve):
        zero = 0
        #Convert incoming valve integer (0-8) to a binary string 
        result = [int(digit) for digit in bin(valve)[2:]]
        #Make sure string is 4 characters in length
        while(len(result)!=4):
            result = [zero] + result
        #print binary address
        #print(result)
        #Write each character (0 or 1) in string 'result' to state of each bit address
        for i in range(len(result)):
            self.d.getFeedback(u3.BitStateWrite(IONumber = 15-i, State = int(result[i])))
            
ValveMaster = VM2000()

def OpenValve(valve):
    ValveMaster.VMOpenValve(valve)
    
def CloseValve(valve):
    ValveMaster.VMCloseValve(valve)
    
if __name__ == '__main__':              # if we're running file directly and not importing it
    OpenValve(1)
    CloseValve(2)
