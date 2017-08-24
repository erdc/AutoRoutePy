# -*- coding: utf-8 -*-
##
##  organize_dem.py
##  AutoRoutePy
##
##  Created by Alan D. Snow, 2016
##  License BSD 3-Clause

from glob import glob
import os
from shutil import copy, move

def organize_dem(input_folder, output_folder=None, dem_ext=".tif"):
    '''
    Reoganzie DEM files into structure needed for AutoRoutePy multiprocessing
    '''
    if output_folder is None:
        output_folder = input_folder
        
    for filename in os.listdir(input_folder):
        if filename.endswith(dem_ext):
            folder_name = os.path.splitext(filename)[0]
            folder_path = os.path.join(output_folder, folder_name)
            dem_file_list = glob("{0}*".format(os.path.join(input_folder, folder_name)))
            try:
                os.mkdir(folder_path)
            except OSError:
                pass
            for dem_file_path in dem_file_list:
                if not os.path.isdir(dem_file_path):
                    dem_file = os.path.basename(dem_file_path)
                    old_location = os.path.join(input_folder,dem_file)
                    new_location = os.path.join(folder_path,dem_file)
                    try:
                        if (input_folder!=output_folder):
                            copy(old_location,
                                 new_location)
                            print("Copied: {0} to {1}".format(old_location, new_location))
                        else:
                            move(old_location,
                                 new_location)
                            print("Moved: {0} to {1}".format(old_location, new_location))
                    except OSError as ex:
                        print(ex)
                        pass
                    
