##################################################
## VasoTracker Pressure Myograph Software
##
## This software provides diameter measurements (inner and outer) of pressurised blood vessels
## Designed to work with Thorlabs DCC1545M
## For additional info see www.vasostracker.com and https://github.com/VasoTracker/VasoTracker
##
##################################################
##
## BSD 3-Clause License
##
## Copyright (c) 2018, VasoTracker
## All rights reserved.
##
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##
## ## * Redistributions of source code must retain the above copyright notice, this
##   list of conditions and the following disclaimer.
##
## * Redistributions in binary form must reproduce the above copyright notice,
##   this list of conditions and the following disclaimer in the documentation
##   and/or other materials provided with the distribution.
##
## * Neither the name of the copyright holder nor the names of its
##   contributors may be used to endorse or promote products derived from
##   this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
## DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
## FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
## SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
## CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
## OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##
##################################################
##
## Author: Penelope F Lawton, Matthew D Lee, and Calum Wilson
## Copyright: Copyright 2018, VasoTracker
## Credits: Penelope F Lawton, Matthew D Lee, and Calum Wilson
## License: BSD 3-Clause License
## Version: 1.4.0
## Maintainer: Calum Wilson
## Email: vasotracker@gmail.com
## Status: Production
## Last updated: 20201028
##
##################################################

## We found the following to be useful:
## https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch09s07.html
## http://code.activestate.com/recipes/82965-threads-tkinter-and-asynchronous-io/
## https://www.physics.utoronto.ca/~phy326/python/Live_Plot.py
## http://forum.arduino.cc/index.php?topic=225329.msg1810764#msg1810764
## https://stackoverflow.com/questions/9917280/using-draw-in-pil-tkinter
## https://stackoverflow.com/questions/37334106/opening-image-on-canvas-cropping-the-image-and-update-the-canvas

from __future__ import division
import numpy as np

# Tkinter imports
import tkinter as tk
from tkinter import *
import tkinter.simpledialog as tkSimpleDialog
import tkinter.messagebox as tmb
import tkinter.filedialog as tkFileDialog
from tkinter import ttk
from PIL import Image, ImageTk  # convert cv2 image to tkinter

E = tk.E
W = tk.W
N = tk.N
S = tk.S
ypadding = 1.5  # ypadding just to save time - used for both x and y

# Other imports
import os
import sys
import time
import datetime
import threading
import random
import queue

import cv2
import csv
from skimage import io
import skimage
from skimage import measure
import serial
import win32com.client
import webbrowser

import colorama

# Add MicroManager to path
"""
import sys
MM_PATH = os.path.join('C:', os.path.sep, 'Program Files','Micro-Manager-1.4')
sys.path.append(MM_PATH)
os.environ['PATH'] = MM_PATH + ';' + os.environ['PATH']
try:
    import MMCorePy
except:
    tmb.showinfo("Warning", "You need to install umanager")
"""
"""
import sys
sys.path.append('C:\Program Files\Micro-Manager-1.4')
import MMCorePy
"""
# import PyQt5
# matplotlib imports
import matplotlib

# matplotlib.use('Qt5Agg')
# matplotlib.use('Qt4Agg', warn=True)
# import matplotlib.backends.tkagg as tkagg
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt

# from matplotlib.backends import backend_qt4agg
from matplotlib import pyplot


class Arduino:
    def __init__(self, PORTS):
        # Open the serial ports
        self.PORTS = PORTS
        self.measured_pressure_1 = None
        self.measured_pressure_2 = None
        self.measured_pressure_avg = None
        self.measured_temperature = None

        ### Finds COM port that the Arduino is on (assumes only one Arduino is connected)
        wmi = win32com.client.GetObject("winmgmts:")
        ArduinoComs = []
        for port in wmi.InstancesOf("Win32_SerialPort"):
            # print port.Name #port.DeviceID, port.Name
            if "Arduino" in port.Name:
                comPort = port.DeviceID
                ArduinoComs.append(comPort)
                #print(
                #    colorama.Fore.GREEN + comPort + colorama.Style.RESET_ALL,
                #    "is Arduino",
                #)
        self.PORTS = []
        for i, comPort in enumerate(ArduinoComs):
            GLOBAL_PORT = serial.Serial(comPort, baudrate=9600, dsrdtr=True)
            # GLOBAL_PORT.setDTR(True)

            self.PORTS.append(GLOBAL_PORT)
            # print(self.PORTS)

    def getports(self):
        return self.PORTS

    def getData(self):
        data = [[] for i in range(2)]
        for i, GLOBAL_PORT in enumerate(self.PORTS):
            try:
                GLOBAL_PORT.flushInput()
                GLOBAL_PORT.flushOutput()
                GLOBAL_PORT.write(b".")  # Note the b prefix for bytes

                startMarker = ord("<")
                endMarker = ord(">")

                ck = b""  # Use bytes instead of str
                x = b"z"  # Use bytes instead of str

                # Wait for the start character
                while ord(x) != startMarker:
                    x = GLOBAL_PORT.read()

                # Save data until the end marker is found
                while ord(x) != endMarker:
                    if ord(x) != startMarker:
                        ck += x  # Concatenate bytes
                    x = GLOBAL_PORT.read()
                data[i].append(ck.decode("utf-8")) 
                #print("data received = ", ck.decode("utf-8"))  # Decode bytes to string
            except:
                ck = b"Nodata:0;Nodata2:0"
            
            data[i].append(ck.decode("utf-8"))  # Decode bytes to string
        
        return data

    def sortdata(self,temppres):
    
        # Initialize variables
        temp = np.nan
        pres1 = np.nan
        pres2 = np.nan

        # Loop through the data from the two Arduinos (tempres contains dummy data if < 2 connected)
        for data in temppres:
            if len(data) > 0:

                # Split the data by Arduino
                val = data[0].strip('\n\r').split(';')
                val = val[:-1]
                val = [el.split(':') for el in val]

                # Get the temperature value
                if val[0][0] == "T1":
                    try:
                        self.measured_temperature = float(val[0][1])
                    except:

                        self.measured_temperature = np.nan
                    #set_temp = float(val[1][1])

                # Get the pressure value
                elif val[0][0] == "P1":
                    try:
                        self.measured_pressure_1  = float(val[0][1])
                        self.measured_pressure_2 = float(val[1][1])
                        self.measured_pressure_avg = np.average([self.measured_pressure_1, self.measured_pressure_2], axis=None)

                    except:
                        self.measured_pressure_1 = np.nan
                        self.measured_pressure_2 = np.nan
                        self.measured_pressure_avg = np.nan

                else:
                    pass
            else:
                pass

        return  self.measured_pressure_1, self.measured_pressure_2, self.measured_pressure_avg, self.measured_temperature


    def sendData(self, pressure):
        print(pressure)
        msg = str(pressure) + "\n"

        #print("message = ", msg)
        x = msg.encode("ascii")  # encode n send
        for i, GLOBAL_PORT in enumerate(self.PORTS):
            GLOBAL_PORT.flushInput()
            GLOBAL_PORT.flushOutput()

            GLOBAL_PORT.write(x)