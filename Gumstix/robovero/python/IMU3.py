from robovero.extras import roboveroConfig
from robovero.internals import robocaller
from math import atan2, degrees
import time


# Initialize pin select registers
#roboveroConfig() need to be called once at least
Gyro_offset=[]

def IMUInit():
		#IMU -- See http://www.agottem.com/robovero_sensors for all the details
	power = 1 
	Acc_x_on = 1 
	Acc_y_on = 1 
	Acc_z_on = 1 
	Acc_freq = 100
	Acc_scale = 2
	Mag_bias = 0
	Mag_freq = 7500
	Mag_scale = 19
	Gyro_x_on = 1
	Gyro_y_on = 1
	Gyro_z_on = 1
	Gyro_freq = 100
	Gyro_scale = 250
	
	print 'Configuration of the sensors\t\t',
	
	robocaller("configAccel","void",power,Acc_x_on,Acc_y_on,Acc_z_on,Acc_freq,Acc_scale)
	robocaller("configMag", "void",power,Mag_bias,Mag_freq,Mag_scale)
	robocaller("configGyro","void",power,Gyro_x_on,Gyro_y_on,Gyro_z_on,Gyro_freq,Gyro_scale)
	
	foo=robocaller("readMag","int")#useless
	
	#Compute the offset of the gyroscope
	Gyro=[]
	global Gyro_offset
	print 'Gyro calibration, please wait!\t\t'
	for n in range(400):
		gyro_raw=robocaller("readGyro","int")
		gyro_tmp=[((x-32768.0)/(32768.0/250.0)) for x in gyro_raw]
		Gyro.append(gyro_tmp)
	Gyro_offset =  [sum(row[n] for row in Gyro)/400 for n in range(3)]#compute the mean of each axis
	print 'Offset: [%0.3f\t%0.3f\t%0.3f]' % (Gyro_offset[0],Gyro_offset[1],Gyro_offset[2])
	Gyro=[]
	
def IMURead():
	Accel=robocaller("readAccel","int")
	Gyro=robocaller("readGyro","int")
	Mag=robocaller("readMag","int")
	return IMUConvert(Accel+Gyro+Mag)

def IMUConvert(values):
	Acc=[((x-32768.0)/(32768.0/2.0)) for x in values[:3]]
	Gyro=[((values[3+n]-32768.0)/(32768.0/250.0)-Gyro_offset[n]) for n in range(3)]
	Mag=[((x-4096.0)/(4096/(19.0/10.0))) for x in values[6:]]
	return Acc, Gyro, Mag

def IMU_heading():
	Acc,Gyro,Mag=IMURead()
	heading= degrees(atan2( (Mag[0]-Mag_offset_x),-(Mag[1]-Mag_offset_y)) )
	return heading
