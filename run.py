#import Libraries
import cv2
import numpy as np
from PIL import  Image
import os
import subprocess
from time import sleep
from pyModbusTCP.client import ModbusClient

#define detect color range (HSV format)
gold_lower= np.array([15,40,110]) 
gold_upper= np.array([30,255,255])

#connect with PLC 
SERVER_HOST = "192.168.8.2" #PLC IP Address   
SERVER_PORT = 502 #default port is 502

client = ModbusClient(host=SERVER_HOST, port=SERVER_PORT)

# Connect to the Modbus server
if not client.is_open:
    if client.open():
        print("Connected to the Modbus server")
    else:
        print("Failed to connect to the Modbus server")

#Correct camera identification using camera name ('USB2.0 Camera')
devices_output = subprocess.check_output(['v4l2-ctl', '--list-devices']).decode('utf-8').split('\n')

for line in devices_output:
	if 'USB2.0 Camera' in line:
		index= devices_output.index(line)
		camid= index +1
		camcall = devices_output[camid]
		busw= camcall.split()[:1]
		camval = busw[0]

#Camera open by Open CV
cap = cv2.VideoCapture(camval)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    #Read PLC signal (M0 memory)
    coil_l = client.read_coils(0,1)
    signal = str(coil_l[0])
    
    ret, frame = cap.read()
    width,height,dim = frame.shape
    left, top = 60,290
    right,bottom =550,460

    #Pre-processing
    crop = frame[top:bottom,left:right,:]
    imgPre = cv2.GaussianBlur(crop,(15,15),5)
    hsvImage = cv2.cvtColor(imgPre, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsvImage,gold_lower,gold_upper)
    mask_ = Image.fromarray(mask)
    bbox = mask_.getbbox()

    if bbox is not None and signal=='True':
        x,y,w,h = bbox
        width = w - x
        hight = h - y
        if  width >= 50 and hight >= 50:    #add threshold for BBOX
        	frame = cv2.rectangle(frame, (60+x,290+y),(60+w,290+h),(0,255,0),2)    #Get BBOX & Sensor Signal = Correct oriantation
        else:
            client.write_single_coil(1, True)   #Get BBOX but its small than threshold, Send signal to PLC M1 memory (M1 HIGH)
            sleep(0.2)
            client.write_single_coil(1, False)
            
    elif bbox is None and signal=='True':   #Get signal but not get BBOX
        print("bad")
        client.write_single_coil(1, True)
        sleep(0.2)
        client.write_single_coil(1, False)
    
     
    cv2.imshow('Output',frame)

    # Kill program
    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

#Clear program
cv2.waitKey(0)
client.close()
cv2.destroyAllWindows()







