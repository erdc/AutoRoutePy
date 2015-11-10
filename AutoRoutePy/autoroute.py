# -*- coding: utf-8 -*-
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
    #REQUIRED ARGS
    stream_file = "" #input stream raster
    dem_file = "" #input dem raster
    spatial_units = "" #input spatial units
    
    #OPTIONAL ARGS
    #set default parameters
    shp_out_file = "" #output flood raster name
    shp_out_shapefile = "" #output flood shapefile name
    dep_out_file = "" #output flood depth raster name
    flood_pnts_name = "" #output flood points file name
    flow_file = "" #flow list variables
    flow_list = "" #flow file variables
    lu_raster = "" #land use raster
    lu_manning_n = "" #land use mannings n table
    x_section_dist = None #default is 1500.0 (sampling x-section distance from center)
    use_prev_d_4_xs = None #defaults is 0 (false)
    q_limit = None #default is 0
    man_n = None #defailt is 0.035
    print_xsections = None #defaults is 0 (false)
    print_vel_dep = None #defaults is 0 (false)
    gen_dir_dist = None #default is 10 (true)
    gen_slope_dist = None #default is 10 (true)
    weight_angles = None #default is 0 (uniform weight)
    thin_non_perpx = None #default is 0 (don't thin out X-Sections)
    elim_non_conctx = None #default is 0 (don't eliminate disconnected X-Sections)
    dist_x_pastwe = None #default is 0 (# cells past waterdepth for X-Section)
    str_limit_val = None #default is 0 (limit of string value - don't have to NULL other stream cells)
    up_str_limit_val = None # default is 9999999999999999 (stream mask threshold)
    degree_manip = None #default is 0.0 (how many degrees are manupulated to catch all boundaries)
    degree_interval = None #default is 1000.0 (interval between degrees if manipulation)
    low_spot_range = None #default is 2 (range cross section will go to find lowest spot on x-section)
    print_strm_mask = None #default is 0 (false)
    pnts_just_3 = None #default is false
    uniform_flow = None #this is the default (Q = Flow_Alpha)
    proportional_flow = None #(Q = Flow_Alpha * Str_Val[r][c])
    exponential_flow = None #(Q = Flow_Alpha * DA^Flow_Beta)
    expon_precip_flow = None #(Q = Flow_Alpha * DA^Flow_Beta Flow_Prec_Const^Flow_Prec_Exp)
    log10_regress_flow = None #(Q = 10 ^ ( Flow_Gamma + Flow_Alpha * DA^Flow_Beta ))
    flow_alpha = None #default is 1.0
    flow_beta = None #default is 1.0
    flow_gamma = None #default is 0.0
    flow_prec_const = None #default is 1.0
    flow_prec_exp = None #default is 1.0
    convert_da_to_sqft = None #default is 1.0 (convert area km2 to sqft)
    convert_da_to_acre = None #default is 1.0 (convert area km2 to acre)
    convert_da_to_sqmi = None #default is 1.0 (convert area km2 to sqmi)
    convert_q_cfs_to_cms = None #default is 1.0 (convert flow cfs to cms)
    str_is_m2 = None #default is 0.0 (units STR values are in - ex. 30 means 30mx30m)

    #list of attributes which require no value    
    _no_value_attr_list = ["uniform_flow", "proportional_flow", "exponential_flow", "expon_precip_flow", "log10_regress_flow"]

    
    def __init__(self, autoroute_executable_location, **kwargs):
        """
        Initialize the class with variables given by the user
        """
        self._autoroute_executable_location = autoroute_executable_location
        self.update_parameters(**kwargs)
        

    def update_parameters(self, **kwargs):
        """
        Update AutoRoute parameters
        """
        #set arguments based off of user input
        for key, value in kwargs.iteritems():
            key = key.lower()
            #debuf\g
            #import pdb
            #pdb.set_trace()
            if key in dir(self) and not key.startswith('_'):
                setattr(self, key, value)
            else:
                raise Exception("Invalid AutoRoute parameter %s." % key)
    
    def generate_input_file(self, file_path):
        """
        Generate AUTO_ROUTE_INPUT.txt file
        """
        print "Generating AutoRoute input file ..."
        try:
            os.remove(file_path)
        except OSError:
            pass
        
        new_file = open(file_path,'w')
        for attr, value in self.__dict__.iteritems():
            if not attr.startswith('_') and value:
                new_file.write("%s %s\n" % (attr, value))
    
        new_file.close()
        
    def update_input_file(self, file_path):
        """
        Update existing input file with new parameters
        """
        if os.path.exists(file_path) and file_path:
            print "Adding missing inputs from AutoRoute input file ..."
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
                elif attr in self._no_value_attr_list:
                    value = True
                #add attribute if exists
                if attr in dir(self) \
                    and not attr.startswith('_'):
                    #set attribute if not set already
                    if not getattr(self, attr):
                        setattr(self, attr, value)
                else:
                    print "Invalid argument" , attr, ". Skipping ..."
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
                autoroute_input_file = "AUTO_ROUTE_INPUT.txt"
            self.generate_input_file(autoroute_input_file)
        else:
            #update existing file
            self.update_input_file(autoroute_input_file)

        #run AutoRoute
        print "Running AutoRoute ..."
        process = Popen([self._autoroute_executable_location, autoroute_input_file], 
                        stdout=PIPE, stderr=PIPE, shell=False)
        out, err = process.communicate()
        if err:
            print err
            raise
        else:
            print 'AutoRoute output:'
            for line in out.split('\n'):
                print line

        print "Time to run AutoRoute: %s" % (datetime.datetime.utcnow()-time_start)


if __name__ == "__main__":
    input_folder = "/home/alan/work/autoroute-io/input/erdc_texas_gulf_region-huc_2_12/30w098"
    auto_mng = AutoRoute('/home/alan/work/scripts/AutoRouteGDAL/source_code/autoroute',
                         stream_file=os.path.join(input_folder, "streamflow_raster.tif"),
                         dem_file=os.path.join(input_folder, "elevation", "hdr.adf"),
                         SHP_Out_File=os.path.join(input_folder,"flood.tif"),
                         SHP_Out_Shapefile=os.path.join(input_folder,"flood_Shp.shp"),
                         )
                         
    auto_mng.run_autoroute(autoroute_input_file=os.path.join(input_folder, "AUTOROUTE_INPUT_FILE.txt"))
            
            
            