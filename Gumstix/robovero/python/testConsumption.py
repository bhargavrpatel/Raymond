# import

from adc2 import LaserRead,ConsumptionRead, ReadAll

import time

#-----------------------------

print 'hello'
while True:
	start_time=time.time()
	data = ReadAll()
	print data
  #read consumption: voltage and current
  #test = ConsumptionRead()
  #print 'Consumption:', voltage,'V \t', current,'A'
	loop_time=time.time()-start_time
	#print 'Time', loop_time,1/loop_time,'\n'
 
  




