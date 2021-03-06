# -*- coding: utf-8 -*-
##
##  autoroute.py
##  AutoRoutePy
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D Snow. All rights reserved.
##  License: BSD-3 Clause

import datetime
import os
from subprocess import Popen, PIPE
#------------------------------------------------------------------------------
#Main Dataset Manager Class
#------------------------------------------------------------------------------
class AutoRoute(object):
    """
    This class is designed to prepare the AUTO_ROUTE_INPUT.txt file and run 
    the AutoRoute program. Additionally, it can perform some GDAL functions
    """
    def __init__(self, autoroute_executable_location, **kwargs):
        """
        Initialize the class with variables given by the user
        """
        self._autoroute_executable_location = autoroute_executable_location

        # REQUIRED ARGS
        self.dem_raster_file_path = ""
        self.stream_info_file_path = ""

        # OPTIONAL ARGS
        # set default parameters
        self.manning_n_raster_file_path = ""
        self.x_section_dist = None
        self.default_manning_n = None
        self.low_spot_range = None  # num cells in center to look to find the lowest point in a cross-section
        self.use_prev_d_4_xsect = None  # use previous depths to calculate XS if value is slightly over
        self.degree_manipulation = None  # This is how many degrees (both positive and negative) that are manipulated to catch all of the boundaries
        self.degree_interval = None  # This is the interval between the degrees of maniputaiton
        self.cells_past_water_depth = None  # cells past the waterdepth for each X-Sections
        self.q_limit = None  # The Q Limit Factor limits erroneous results by stopping too much overflow
        self.eliminate_xsection = None  # ELIMINATE the Cross-Sections that don't fully Connect
        self.xsect_file_path = ""
        self.out_flood_map_raster_path = ""
        self.out_flood_depth_raster_path = ""
        self.out_flood_map_shapefile_path = ""

        self.update_parameters(**kwargs)


    def update_parameters(self, **kwargs):
        """
        Update AutoRoute parameters
        """
        #set arguments based off of user input
        for key, value in kwargs.items():
            key = key.lower()
            if key in dir(self) and not key.startswith('_'):
                setattr(self, key, value)
            else:
                raise Exception("Invalid AutoRoute parameter %s." % key)
    
    def generate_input_file(self, file_path):
        """
        Generate AUTOROUTE_INPUT_FILE.txt file
        """
        try:
            os.remove(file_path)
        except OSError:
            pass
        
        new_file = open(file_path,'w')
        for attr, value in sorted(list(self.__dict__.items())):
            if not attr.startswith('_') and value:
                new_file.write("%s %s\n" % (attr, value))
    
        new_file.close()
        
    def update_input_file(self, file_path):
        """
        Update existing input file with new parameters
        """
        if os.path.exists(file_path) and file_path:
            old_file = open(file_path, 'r')
            for line in old_file:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                line_split = line.split()
                attr = line_split[0].lower()
                value = None
                if len(line_split)>1:
                    value = line_split[1]
                #add attribute if exists
                if attr in dir(self) \
                    and not attr.startswith('_'):
                    #set attribute if not set already
                    if not getattr(self, attr):
                        setattr(self, attr, value)
                else:
                    print("Invalid argument" + attr + ". Skipping ...")
            old_file.close()
            
            self.generate_input_file(file_path)
        else:
            raise Exception("AutoRoute input file to update not found.")
    
    def run_autoroute(self, autoroute_input_file=""):
        """
        Run AutoRoute program and generate file based on inputs
        """
    
        time_start = datetime.datetime.utcnow()
    
        if not autoroute_input_file or not os.path.exists(autoroute_input_file):
            #generate input file if it does not exist
            if not autoroute_input_file:
                autoroute_input_file = "AUTOROUTE_INPUT_FILE.txt"
            self.generate_input_file(autoroute_input_file)
        else:
            #update existing file
            self.update_input_file(autoroute_input_file)

        #run AutoRoute
        print("Running AutoRoute ...")
        process = Popen([self._autoroute_executable_location, autoroute_input_file], 
                        stdout=PIPE, stderr=PIPE, shell=False)
        out, err = process.communicate()
        if err:
            print(err)
            raise
        else:
            print('AutoRoute output:')
            for line in out.split(b'\n'):
                print(line)

        print("Time to run AutoRoute: %s" % (datetime.datetime.utcnow()-time_start))
