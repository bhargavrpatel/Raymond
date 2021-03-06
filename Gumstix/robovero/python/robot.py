from robovero.internals import robocaller, store_data #store_data is used to write the data to a file
from robovero.extras import roboveroConfig
print 'Robot configuration'
roboveroConfig()
from uart2 import UARTInit, UARTConvert, FloatToBytes
from adc2 import ADCConvert, BatteryVoltage, DistanceInit
from IMU3 import IMUInit, IMUConvert
from math import pi, degrees, radians, cos, sin, sqrt, hypot,atan2
from algorithm import Normalize, Algorithm, DistanceControl, HeadingControl
import time

#------ Global Variables -------
#Power
voltage =0
current =0
filtered_voltage = 12 #Battery voltage of 12V at the beginning
energy_consumme=0.0
#Odometry
speed=0.0
rot_speed=0.0
heading=0.0
direction=heading
pose_x = 0
pose_y = 0
odom=[0,0,0,0]
speed_odom = 0
rot_speed_odom = 0
pose_x_odom = 0
pose_y_odom = 0
heading_odom = 0
direction_odom = heading_odom
wheel_speeds = [0,0,0,0]
odom0 = [0,0,0]
odom1 = [0,0,0]
odom2 = [0,0,0]
odom3 = [0,0,0]
#Laser
distances = DistanceInit(3)
raw_distance = distances[0]
distance = raw_distance
#IMU
Accel=[0,0,0,0]
Gyro=[0,0,0,0]
Mag=[0,0,0,0]
#Time
loop_time = 0.03 #30ms
MinLoopTime = 1/50.0 # 50Hz
first_time=time.time()
#UART
messagenumber = 0
#Robot
robot_radius = 0.2 # 200mm


#-------------- Functions ---------------
def AllInOne(speed, rot_speed, direction):
	global messagenumber
	message_send = FloatToBytes(speed, rot_speed, direction)
	message_send.append(messagenumber)
	#print hex(message_send[13])
	messagenumber=messagenumber+1
	return robocaller("AllInOne","int",message_send)
	
def Localization(speed, rotational_speed, pose_x, pose_y, heading, direction, delta_t):
	pose_x = pose_x + speed*cos(heading+direction)*delta_t
	pose_y = pose_y + speed*sin(heading+direction)*delta_t
	heading = heading + rotational_speed*delta_t
	return pose_x, pose_y, Normalize(heading)
	
def Speeds2Commands(wheel_speeds):
	global robot_radius
	coef = sqrt(2)/4 # coef = 1/ (sin(pi/4)*4 )
	speed_x = coef * ( sum(wheel_speeds[0:2]) - sum(wheel_speeds[2:]) )
	speed_y = coef * ( -wheel_speeds[0] + sum(wheel_speeds[1:3]) - wheel_speeds[-1])
	rot_speed = -sum(wheel_speeds) /(4.0*robot_radius)
	speed= hypot(speed_x, speed_y)
	direction = atan2(speed_y,speed_x)
	return speed, direction, rot_speed

def MedianFilter(datas,new_data):
	datas.append(new_data)
	datas = datas[1:]
	sorted_data = sorted(datas)
	size = len(sorted_data)
	if size % 2 == 1:
		median = sorted_data[(size - 1) / 2]
	else:
		median = sum(sorted_data[size/2 - 1:size/2 + 1])/2
	return datas, median
	
def CheckBattery(new_voltage):
	global filtered_voltage
	coef = 0.01
	filtered_voltage = (1-coef)*filtered_voltage + coef*new_voltage
	if filtered_voltage < 9:
		stopmotors=[0 for n in range(13)] ; stopmotors[-1]=69
		robocaller("AllInOne","void",stopmotors)
		print 'Motors stopped'
		time.sleep(1)
		exit()
		
def Store_data(data_list):
	global store_data
	for item in data_list:
		store_data.write("%s \t" % item)
	store_data.write("\n")
	 
#-----------------------------

UARTInit()
print 'Battery voltage is %0.1fV' % BatteryVoltage()
IMUInit()


print 'Initialization: done --> Start\n'
time.sleep(0.5) # To have time to read the previous print
time_start=time.time()


while True:
	
	#Read all sensors and send/receive UART
	message_receive = AllInOne(speed, rot_speed, direction) 
	#print 'Received', message_receive #debug
	if message_receive is not None:
		if len(message_receive) ==32:
			message_receive=message_receive[2:]
			ret=UARTConvert(message_receive[0:18])
			if ret != 0:
				odom = ret
				odom0, odom[0] = MedianFilter(odom0,odom[0])
				odom1, odom[1] = MedianFilter(odom1,odom[1])
				odom2, odom[2] = MedianFilter(odom2,odom[2])
				odom3, odom[3] = MedianFilter(odom3,odom[3])
			raw_distance,voltage,current=ADCConvert(message_receive[18:21])
			distances, distance = MedianFilter(distances,raw_distance)
			Accel,Gyro,Mag = IMUConvert(message_receive[21:])
			time_sensors=time.time()
			#print 'Odometry: %0.2f m \t %0.2f m \t %0.2f m \t %0.2f m' % (odom[0],odom[1],odom[2],odom[3])
			#print 'ADC: %0.2f m \t %0.0f mA \t %0.1f V ' % (distance, current*1000, voltage)
			#print 'IMU: %0.2f\t%0.2f\t%0.2f\t\t%0.2f\t%0.2f\t%0.2f\t\t%0.3f\t%0.3f\t%0.3f' %(Accel[0],Accel[1],Accel[2],Gyro[0],Gyro[1],Gyro[2],Mag[0],Mag[1],Mag[2])
	
	#Compute energy consumption
	energy_consumme = energy_consumme + voltage*current*loop_time
	CheckBattery(voltage)#Stops motors if Vbatt<9V
				
	#Localization from command
	pose_x, pose_y, heading =  Localization(speed, -radians(Gyro[2])*1.18, pose_x, pose_y, heading, direction, loop_time)#gyro's values are in dps and 1.18 is a calibration factor
	#Localization from odometry
	wheel_speeds=[odom[n]/0.020 for n in range(4)]
	speed_odom, direction_odom, rot_speed_odom=Speeds2Commands(wheel_speeds)
	pose_x_odom, pose_y_odom, heading_odom = Localization(speed_odom, -radians(Gyro[2])*1.18, pose_x_odom, pose_y_odom, heading_odom, direction_odom, loop_time)
  
  #compute next direction
	speed, rot_speed, direction = Algorithm(pose_x, pose_y, heading, distance)
	#rot_speed = HeadingControl(heading, 0)
	#print 'Command', speed, rot_speed, degrees(direction)
 	
 	time_end=time.time()
	loop_time=time_end-time_start
	if loop_time < MinLoopTime:
		time.sleep(MinLoopTime-loop_time)
	time_end=time.time()
	loop_time=time_end-time_start
	time_start=time_end
	
	#print 'Time: %0.1f ms\t Frequency: %0.1f Hz' % (loop_time*1000.0, 1.0/loop_time)
	Store_data( ( (time.time()-first_time),loop_time,energy_consumme,voltage,current,speed, rot_speed, direction, odom[0],odom[1],odom[2],odom[3],heading, pose_x, pose_y, heading_odom, pose_x_odom, pose_y_odom,Accel[0],Accel[1],Accel[2],Gyro[0],Gyro[1],Gyro[2],Mag[0],Mag[1],Mag[2],raw_distance,distance ) )


#led=open('/sys/devices/platform/leds-gpio/leds/overo:blue:gpio22/brightness','w')
#led.write('0')
#led.close()
