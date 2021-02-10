#RUN this python in super user mode
#> sudo su
#> python3 datagen_script.py

#don't run with sudo datagen_script.py: it will generate wrong results

import os
import csv

# 0. Open csv file to store the data
fields = ['RAM(MB)', 'Cores', 'Workload(%)', 'YOLOtime(s)']
ram =  2000 #MB Default RAM value
ram_low = 1000
ram_high = 3000
epoch = 40 #number of experiments
print("Starting....")
#====================================================1. Core vs Execution Time
# Create File to store data
filename = 'cpu_cores_time.csv'
if not os.path.exists(filename):
    print('creating new file')
    csvfile = open(filename, 'a')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
else:
    print('opening file')
    csvfile = open(filename, 'a')
    csvwriter = csv.writer(csvfile)

#Loop to evaluate YOLO Execution Time
for num_cpu_cores in range(1, 5, 1):
    core_list = '' # generate list of cores: string
    for cores in range(num_cpu_cores):
        core_list += '{}'.format(cores) #use core 11, 12
        if cores < num_cpu_cores-1:
            core_list += ','
    
    #Assign Program to Particular Cores
    bash_pid = os.getppid() #get the ID of bash program
    print(bash_pid)
    print(os.popen("taskset -cp {} {}".format(core_list, bash_pid)).read()) #limit the cores
    print(os.popen("taskset -cp {} {}".format(core_list, os.getpid())).read())
    
    #Generate CPU Workload to 40%
    workload_cpu_stress = 40 # % load on the CPU due to workload to simulate bg process   
    workload_pid = os.popen("stress-ng -c {} -l {} > /dev/null 2>&1 & echo $!".format(num_cpu_cores, workload_cpu_stress)).read().strip('\n')
    print('PID of workload is {} and number of cores used is {}'.format(workload_pid, num_cpu_cores))
    
    #Run Experiment for 50 time
    for i in range(epoch):              
        #Run YOLO Program
        try:
            yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
        except:
            print("program could not run")
        # Save Data to file
        data_row = [ram, num_cpu_cores, workload_cpu_stress, yolo_time] #format data for csv
        csvwriter.writerow(data_row) #write the data
    
    # Kill the workload process for next experiment
    os.popen("kill -9 {}".format(workload_pid))

# Close the csv file
csvfile.close()
print("Core vs Exec Time Finished")
#====================================================2. CPU Workload vs Execution Time
# Create File to store data
filename = 'cpu_workload_time.csv'
if not os.path.exists(filename):
    print('creating new file')
    csvfile = open(filename, 'a')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
else:
    print('opening file')
    csvfile = open(filename, 'a')
    csvwriter = csv.writer(csvfile)

#Loop to evaluate YOLO Execution Time
for workload_cpu_stress in range(10, 60, 10): #for workload 10%, 20%...60%
    num_cpu_cores = 1 # assign to only single core
    core_list = '' # generate list of cores: string
    for cores in range(num_cpu_cores):
        core_list += '{}'.format(cores)
        if cores < num_cpu_cores-1:
            core_list += ','
    
    #Assign Program to Particular Cores
    bash_pid = os.getppid() #get the ID of bash program
    print(bash_pid)
    print(os.popen("taskset -cp {} {}".format(core_list, bash_pid)).read()) #limit the cores
    print(os.popen("taskset -cp {} {}".format(core_list, os.getpid())).read())
    
    #Generate CPU Workload   
    workload_pid = os.popen("stress-ng -c {} -l {} > /dev/null 2>&1 & echo $!".format(num_cpu_cores, workload_cpu_stress)).read().strip('\n')
    print('PID of workload is {} and number of cores used is {}'.format(workload_pid, num_cpu_cores))
    
    #Run Experiment for 50 time
    for i in range(epoch):              
        #Run YOLO Program
        try:
            yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
        except:
            print("program could not run")
        # Save Data to file
        data_row = [ram, num_cpu_cores, workload_cpu_stress, yolo_time] #format data for csv
        csvwriter.writerow(data_row) #write the data
    
    # Kill the workload process for next experiment
    os.popen("kill -9 {}".format(workload_pid))

# Close the csv file
csvfile.close()
print("Workload vs Exec Time Finished")
#====================================================3. RAM vs Execution Time
# Create File to store data
filename = 'cpu_ram_time.csv'
if not os.path.exists(filename):
    print('creating new file')
    csvfile = open(filename, 'a')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
else:
    print('opening file')
    csvfile = open(filename, 'a')
    csvwriter = csv.writer(csvfile)

#Loop to evaluate YOLO Execution Time
for ram in range(ram_low, ram_high, 500): #for workload 10%, 20%...60%
    num_cpu_cores = 1 # assign to only single core
    core_list = '' # generate list of cores: string
    for cores in range(num_cpu_cores):
        core_list += '{}'.format(cores)
        if cores < num_cpu_cores-1:
            core_list += ','
    
    #Assign Program to Particular Cores
    bash_pid = os.getppid() #get the ID of bash program
    print(bash_pid)
    print(os.popen("taskset -cp {} {}".format(core_list, bash_pid)).read()) #limit the cores
    print(os.popen("taskset -cp {} {}".format(core_list, os.getpid())).read())
    
    #Generate CPU Workload
    workload_cpu_stress = 40 # % load on the CPU due to workload to simulate bg process   
    workload_pid = os.popen("stress-ng -c {} -l {} > /dev/null 2>&1 & echo $!".format(num_cpu_cores, workload_cpu_stress)).read().strip('\n')
    print('PID of workload is {} and number of cores used is {}'.format(workload_pid, num_cpu_cores))
    
    #Run Experiment for 50 time
    for i in range(epoch):              
        #Run YOLO Program
        try:
            yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
        except:
            print("program could not run")
        # Save Data to file
        data_row = [ram, num_cpu_cores, workload_cpu_stress, yolo_time] #format data for csv
        csvwriter.writerow(data_row) #write the data
    
    # Kill the workload process for next experiment
    os.popen("kill -9 {}".format(workload_pid))

# Close the csv file
csvfile.close()
print("Finished!") 
