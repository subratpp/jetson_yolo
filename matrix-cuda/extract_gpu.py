import re
def gpu_workload(filename): 
    max_use = 0
    with open(filename) as fp:
        lines = fp.readlines()
        for line in lines:
            gpu = re.search(r'GR3D_FREQ (.*?)%', line).group(1)
            if int(gpu) > max_use:
                max_use = float(gpu)
    return max_use
    
print(gpu_worklaod("matmul1000.txt"))
