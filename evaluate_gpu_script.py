#RUN this python in super user mode
#> sudo su
#> python3 datagen_script.py

#don't run with sudo datagen_script.py: it will generate wrong results

import os
import csv
import re
import time

#find average workload from the data file
def gpu_workload(filename): 
    avg_use = 0
    count = 0
    with open(filename) as fp:
        lines = fp.readlines()
        for line in lines:
            gpu = re.search(r'GR3D_FREQ (.*?)%', line).group(1)
            if int(gpu) > 0:
                avg_use += float(gpu)
                count +=1
    os.remove(filename)
    return avg_use/count

#csv file to store the data
fields = ['RAM(MB)', 'Cores', 'Workload_GPU(%)', 'Workload_CPU(%)', 'YOLOtime(s)']
ram =  3000 #MB Default RAM value
ram_low = 2000
ram_high = 3000
epoch = 2 #number of experiments

#=================================================== 1. Core vs Execution Time
filename = 'gpu_cores_time.csv'
if not os.path.exists(filename):
    print('creating new file')
    csvfile = open(filename, 'a')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
else:
    print('opening file')
    csvfile = open(filename, 'a')
    csvwriter = csv.writer(csvfile)

# Loop over Core values
for num_cpu_cores in range(1, 5, 1):   
    # Assing core to the process
    # num_cpu_cores = 1 # number of CPU cores used
    core_list = '' # generate list of cores: string
    for cores in range(num_cpu_cores):
        core_list += "{}".format(cores+10) #run on core 11
        if cores < num_cpu_cores-1:
            core_list += ','

    # Taskset CPU to partiicular cores
    bash_pid = os.getppid() #get the ID of bash program
    print(bash_pid)
    print(os.popen("taskset -cp {} {}".format(core_list, bash_pid)).read()) #limit the cores
    print(os.popen("taskset -cp {} {}".format(core_list, os.getpid())).read())

    # Generate Workload
    workload_cpu_stress = 40 # % load on the CPU due to workload to simulate bg process   
    workload_pid_cpu = os.popen("stress-ng -c {} -l {} > /dev/null 2>&1 & echo $!".format(num_cpu_cores, workload_cpu_stress)).read().strip('\n')
    print('PID of workload is {} and number of cores used is {}'.format(workload_pid_cpu, num_cpu_cores))
    
    # Generate GPU Workload: Matrix Multiplication
    os.popen("tegrastats --interval 500 --logfile gpustat.tmp &") #start monitoring tegras workload
    matrix = 100 #matrix shape
    workload_pid = os.popen("./workload {} {} {} > /dev/null 2>&1 & echo $!".format(matrix, matrix, matrix)).read().strip('\n')
    print('PID of workload is {}'.format(workload_pid)) 

    time.sleep(3) #wait for 3 sec
    os.popen("tegrastats --stop") #stop monitoring tegras workload
    
    #compute workload from the .tmp file
    try: 
        workload_gpu = gpu_workload("gpustat.tmp") #it deleted the file after computing average
    except:
        workload_gpu = 0 #no values found
    
    for i in range(epoch):
        #Run YOLO Program
        try:
            #===For CPU + GPU
            yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet detect cfg/yolov3-tiny.cfg yolov3-tiny.weights data/dog.jpg | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
            #===For Only GPU
            # yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet classifier predict cfg/imagenet1k.data cfg/densenet201.cfg densenet201.weights data/eagle.jpg 2>&1 | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
        except:
            print("program could not run")
        #fetch GPU workload time
        
        
        data_row = [ram, num_cpu_cores, workload_gpu, workload_cpu_stress, yolo_time] #format data for csv
        csvwriter.writerow(data_row) #write the data
    
    # Kill the workload process
    os.popen("kill -9 {}".format(workload_pid))
    os.popen("kill -9 {}".format(workload_pid_cpu))

# close the csv file
csvfile.close() 

#=================================================== 2. GPU Workload vs Execution Time
# filename = 'gpu_workloadgpu_time.csv'
# if not os.path.exists(filename):
#     print('creating new file')
#     csvfile = open(filename, 'a')
#     csvwriter = csv.writer(csvfile)
#     csvwriter.writerow(fields)
# else:
#     print('opening file')
#     csvfile = open(filename, 'a')
#     csvwriter = csv.writer(csvfile)

# # Loop over GPU workload values
# for matrix in range(1000, 8000, 1000):   
#     # Assing core to the process
#     num_cpu_cores = 1 # number of CPU cores used
#     core_list = '' # generate list of cores: string
#     for cores in range(num_cpu_cores):
#         core_list += "{}".format(cores+10) #run on core 11
#         if cores < num_cpu_cores-1:
#             core_list += ','

#     # Taskset CPU to partiicular cores
#     bash_pid = os.getppid() #get the ID of bash program
#     print(bash_pid)
#     print(os.popen("taskset -cp {} {}".format(core_list, bash_pid)).read()) #limit the cores
#     print(os.popen("taskset -cp {} {}".format(core_list, os.getpid())).read())

#     # Generate Workload
#     workload_cpu_stress = 40 # % load on the CPU due to workload to simulate bg process   
#     workload_pid_cpu = os.popen("stress-ng -c {} -l {} > /dev/null 2>&1 & echo $!".format(num_cpu_cores, workload_cpu_stress)).read().strip('\n')
#     print('PID of workload is {} and number of cores used is {}'.format(workload_pid_cpu, num_cpu_cores))
    
#     # Generate GPU Workload: Matrix Multiplication
#     # matrix = 7000 #matrix shape
#     workload_pid = os.popen("./workload {} {} {} > /dev/null 2>&1 & echo $!".format(matrix, matrix, matrix)).read().strip('\n')
#     print('PID of workload is {}'.format(workload_pid))  
    
#     for i in range(epoch):
#         #Run YOLO Program
#         try:
#             #===For CPU + GPU
#             yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
#             #===For Only GPU
#             # yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet classifier predict cfg/imagenet1k.data cfg/densenet201.cfg densenet201.weights data/eagle.jpg 2>&1 | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
#         except:
#             print("program could not run")
#         #fetch GPU workload time
#         try:
#             workload_res = os.popen("nvidia-smi | awk '/{}/{{print $6}}'".format(workload_pid)).read()
#             workload_gpu = (float(re.findall(r'[0-9 .]+', workload_res)[0])/8029)*100
#         except:
#             workload_gpu = '' #no values found
        
#         data_row = [ram, num_cpu_cores, workload_gpu, workload_cpu_stress, yolo_time] #format data for csv
#         csvwriter.writerow(data_row) #write the data
    
#     # Kill the workload process
#     os.popen("kill -9 {}".format(workload_pid))
#     os.popen("kill -9 {}".format(workload_pid_cpu))

# # close the csv file
# csvfile.close() 


# #=================================================== 3. CPU Workload vs Execution Time
# filename = 'gpu_workloadcpu_time.csv'
# if not os.path.exists(filename):
#     print('creating new file')
#     csvfile = open(filename, 'a')
#     csvwriter = csv.writer(csvfile)
#     csvwriter.writerow(fields)
# else:
#     print('opening file')
#     csvfile = open(filename, 'a')
#     csvwriter = csv.writer(csvfile)

# #4. Loop over CPU workload values
# for workload_cpu_stress in range(10, 80, 10):   
#     # Assing core to the process
#     num_cpu_cores = 1 # number of CPU cores used
#     core_list = '' # generate list of cores: string
#     for cores in range(num_cpu_cores):
#         core_list += "{}".format(cores+10) #run on core 11
#         if cores < num_cpu_cores-1:
#             core_list += ','

#     # Taskset CPU to partiicular cores
#     bash_pid = os.getppid() #get the ID of bash program
#     print(bash_pid)
#     print(os.popen("taskset -cp {} {}".format(core_list, bash_pid)).read()) #limit the cores
#     print(os.popen("taskset -cp {} {}".format(core_list, os.getpid())).read())

#     # workload_cpu_stress = 40 # % load on the CPU due to workload to simulate bg process   
#     # Generate Workload
#     workload_pid_cpu = os.popen("stress-ng -c {} -l {} > /dev/null 2>&1 & echo $!".format(num_cpu_cores, workload_cpu_stress)).read().strip('\n')
#     print('PID of workload is {} and number of cores used is {}'.format(workload_pid_cpu, num_cpu_cores))
    
#     # Generate GPU Workload: Matrix Multiplication
#     matrix = 7000 #matrix shape
#     workload_pid = os.popen("./workload {} {} {} > /dev/null 2>&1 & echo $!".format(matrix, matrix, matrix)).read().strip('\n')
#     print('PID of workload is {}'.format(workload_pid))  
    
#     for i in range(epoch):
#         #Run YOLO Program
#         try:
#             #===For CPU + GPU
#             yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
#             #===For Only GPU
#             # yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet classifier predict cfg/imagenet1k.data cfg/densenet201.cfg densenet201.weights data/eagle.jpg 2>&1 | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
#         except:
#             print("program could not run")
#         #fetch GPU workload time
#         try:
#             workload_res = os.popen("nvidia-smi | awk '/{}/{{print $6}}'".format(workload_pid)).read()
#             workload_gpu = (float(re.findall(r'[0-9 .]+', workload_res)[0])/8029)*100
#         except:
#             workload_gpu = '' #no values found
        
#         data_row = [ram, num_cpu_cores, workload_gpu, workload_cpu_stress, yolo_time] #format data for csv
#         csvwriter.writerow(data_row) #write the data
    
#     # Kill the workload process
#     os.popen("kill -9 {}".format(workload_pid))
#     os.popen("kill -9 {}".format(workload_pid_cpu))

# # close the csv file
# csvfile.close() 

# #=================================================== 4. RAM vs Execution Time
# filename = 'gpu_ram_time.csv'
# if not os.path.exists(filename):
#     print('creating new file')
#     csvfile = open(filename, 'a')
#     csvwriter = csv.writer(csvfile)
#     csvwriter.writerow(fields)
# else:
#     print('opening file')
#     csvfile = open(filename, 'a')
#     csvwriter = csv.writer(csvfile)

# #4. Loop over RAM values
# for ram in range(ram_low, ram_high, 1000):   
#     # Assing core to the process
#     num_cpu_cores = 1 # number of CPU cores used
#     core_list = '' # generate list of cores: string
#     for cores in range(num_cpu_cores):
#         core_list += "{}".format(cores+10) #run on core 11
#         if cores < num_cpu_cores-1:
#             core_list += ','

#     # Taskset CPU to partiicular cores
#     bash_pid = os.getppid() #get the ID of bash program
#     print(bash_pid)
#     print(os.popen("taskset -cp {} {}".format(core_list, bash_pid)).read()) #limit the cores
#     print(os.popen("taskset -cp {} {}".format(core_list, os.getpid())).read())

#     # Generate Workload
#     workload_cpu_stress = 40 # % load on the CPU due to workload to simulate bg process   
#     workload_pid_cpu = os.popen("stress-ng -c {} -l {} > /dev/null 2>&1 & echo $!".format(num_cpu_cores, workload_cpu_stress)).read().strip('\n')
#     print('PID of workload is {} and number of cores used is {}'.format(workload_pid_cpu, num_cpu_cores))
    
#     # Generate GPU Workload: Matrix Multiplication
#     matrix = 7000 #matrix shape
#     workload_pid = os.popen("./workload {} {} {} > /dev/null 2>&1 & echo $!".format(matrix, matrix, matrix)).read().strip('\n')
#     print('PID of workload is {}'.format(workload_pid))  
    
#     for i in range(epoch):
#         #Run YOLO Program
#         try:
#             #===For CPU + GPU
#             yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
#             #===For Only GPU
#             # yolo_time = os.popen("sudo systemd-run --scope -p MemoryLimit={}M ./darknet classifier predict cfg/imagenet1k.data cfg/densenet201.cfg densenet201.weights data/eagle.jpg 2>&1 | awk '/Predicted/{{print $4}}' ".format(ram)).read().strip('\n')
#         except:
#             print("program could not run")
#         #fetch GPU workload time
#         try:
#             workload_res = os.popen("nvidia-smi | awk '/{}/{{print $6}}'".format(workload_pid)).read()
#             workload_gpu = (float(re.findall(r'[0-9 .]+', workload_res)[0])/8029)*100
#         except:
#             workload_gpu = '' #no values found
        
#         data_row = [ram, num_cpu_cores, workload_gpu, workload_cpu_stress, yolo_time] #format data for csv
#         csvwriter.writerow(data_row) #write the data
    
#     # Kill the workload process
#     os.popen("kill -9 {}".format(workload_pid))
#     os.popen("kill -9 {}".format(workload_pid_cpu))

# # close the csv file
# csvfile.close() 




