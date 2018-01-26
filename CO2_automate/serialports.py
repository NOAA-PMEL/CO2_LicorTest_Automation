# -*- coding: utf-8 -*-
"""
Created on Fri Jan 26 08:17:01 2018

@author: casari
"""

import sys
import glob
import serial


def Find_Serial():
    portnames = []
    
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i+1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported Platform')
        
    

    portnames[:] = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            portnames.append(port)
        except (OSError,serial.SerialException):
            pass
        
    return portnames





if __name__ == '__main__':
    
    serialnames = Find_Serial()
    
    print(serialnames)