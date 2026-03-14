#remember to configure and enable I2C in sudo raspi-config.

from mpu6050 import mpu6050 as IMU #install mpu6050-raspberrypi
from time import sleep as wait
import threading as thr

#// ============ SETTINGS ============ //#
quitKeyCode='e'

#// ============ AUTO VARS ============ //#
#// do not touch these pls, 
# or you'll ruin the program
IMUanchorIP=0x68
IMUbasketIP=0x69
IMUdata={} #/ Data Dictionary

# __________________________________________________________________________
#// DEFINITION: Loop module for capturing gyro and acceleration IMU data. //
def IMUdata_module():
    global IMUdata
    IMUanchor=IMU(IMUanchorIP) #// Attached to robot, calculates incline and angle.
    while True:
        IMUdata["Acceleration"]=IMUanchor.get_accel_data()
        IMUdata["Gyro"]=IMUanchor.get_gyro_data()
        wait(seconds=1)


#// ============ MAIN PROGRAM ============ //#
IMUt=thr.Thread(target=IMUdata_module)
IMUt.start()
IMUt.join()