# -*- coding: utf-8 -*-
from multiprocessing import cpu_count
import os
import re
import sys

try:
    from psutil import virtual_memory
except ImportError:
    print "psutil unable to be imported. If you would like to use multiprocessing", \
          "mode, please install psutil (i.e. pip install psutil)."
    pass

#----------------------------------------------------------------------------------------
# HELPER FUNCTIONS
#----------------------------------------------------------------------------------------
class CaptureStdOutToLog(object):
    def __init__(self, out_file_path):
        self.out_file_path = out_file_path
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = open(self.out_file_path, 'w')
        return self
    def __exit__(self, *args):
        sys.stdout.close()
        sys.stdout = self._stdout
        
def case_insensitive_file_search(directory, pattern):
    """
    Looks for file with pattern with case insensitive search
    """
    try:
        return os.path.join(directory,
                            [filename for filename in os.listdir(directory) \
                             if re.search(pattern, filename, re.IGNORECASE)][0])
    except IndexError:
        print pattern, "not found"
        raise

def get_valid_watershed_list(input_directory):
    """
    Get a list of folders formatted correctly for watershed-subbasin
    """
    valid_input_directories = []
    for directory in os.listdir(input_directory):
        if os.path.isdir(os.path.join(input_directory, directory)) \
            and len(directory.split("-")) == 2:
            valid_input_directories.append(directory)
        else:
            print directory, "incorrectly formatted. Skipping ..."
    return valid_input_directories

def get_watershed_subbasin_from_folder(folder_name):
    """
    Get's the watershed & subbasin name from folder
    """
    input_folder_split = folder_name.split("-")
    watershed = input_folder_split[0].lower()
    subbasin = input_folder_split[1].lower()
    return watershed, subbasin
    
def get_valid_num_cpus(num_cpus):
    """
    Retrieves the valid number of cpus based on computer specs
    """
    #set number of cpus to use (recommended 3 GB per cpu)
    total_cpus = cpu_count()
    mem = virtual_memory()
    recommended_max_num_cpus = max(1, int(mem.total  * 1e-9 / 3))
    if num_cpus <= 0:
        num_cpus = total_cpus
        num_cpus = min(recommended_max_num_cpus, total_cpus)
    if num_cpus > total_cpus:
        num_cpus = total_cpus
        print("Number of cpus entered is greater then available cpus. Using all avalable cpus ...")
    if num_cpus > recommended_max_num_cpus:
        print("WARNING: Number of cpus allotted ({0}) exceeds maximum recommended ({1}). " \
              "This may cause memory issues ...".format(num_cpus, recommended_max_num_cpus))
    print("Running with {0} CPUS".format(num_cpus))
    return num_cpus
