# -*- coding: utf-8 -*-
import datetime
import os
from subprocess import Popen, PIPE
try:
    from osgeo import gdal, ogr, osr
except ImportError:
    import gdal, ogr, osr

gdal.AllRegister()
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
    
    def __init__(self, autoroute_executable_location, **kwargs):
        """
        Initialize the class with variables given by the user
        """
        self.autoroute_executable_location = autoroute_executable_location
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
            if key in dir(self) and key != "autoroute_executable_location":
                setattr(self, key, value)
            else:
                print("Invalid argument" , key, ". Skipping ...")
    
    def generate_input_file(self, file_path):
        """
        Prepare AUTO_ROUTE_INPUT.txt file
        """
        print("Generating AutoRoute input file ...")
        try:
            os.remove(file_path)
        except OSError:
            pass
        
        new_file = open(file_path,'w')
        for attr, value in self.__dict__.iteritems():
            if not attr.startswith('_') \
                and value \
                and attr != "shp_out_shapefile" \
                and attr != "autoroute_executable_location":
                    
                new_file.write("%s %s\n" % (attr, value))
    
        new_file.close()
    
    def run_autoroute(self, autoroute_input_file=""):
        """
        Run AutoRoute program and generate file based on inputs
        """
    
        time_start = datetime.datetime.utcnow()
    
        if not autoroute_input_file:
            autoroute_input_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                "AUTO_ROUTE_INPUT.txt")
                                                
            self.generate_input_file(autoroute_input_file)

        #run AutoRoute
        print("Running AutoRoute ...")
        process = Popen([self.autoroute_executable_location, autoroute_input_file], 
                        stdout=PIPE, stderr=PIPE, shell=False)
        out, err = process.communicate()
        if err:
            print err
            raise
        else:
            print('AutoRoute output:')
            for line in out.split('\n'):
                print line

        print("Time to run AutoRoute: %s" % (datetime.datetime.utcnow()-time_start))
        
        if self.shp_out_shapefile and os.path.exists(self.shp_out_file) and self.shp_out_shapefile:
            self.convert_raster_to_shapefile(self.shp_out_file, self.shp_out_shapefile)
        
    def convert_raster_to_shapefile(self, raster_name, shapefile_name="", raster_band=1):
        """
        Converts a raster to a shapefile
        Adapted from https://svn.osgeo.org/gdal/trunk/gdal/swig/python/scripts/gdal_polygonize.py
        """
        time_start_convert = datetime.datetime.utcnow()
        #open the raster
        gdal_raster = gdal.Open( raster_name )
        if gdal_raster is None:
            print("Unable to open", raster_name)
            return
        gdal_raster_band = gdal_raster.GetRasterBand(raster_band) 
        gdal_raster_mask = gdal_raster_band.GetMaskBand()
        
        #create output shapefile
        if not shapefile_name:
            shapefile_name = "%s_shp.shp" % os.path.basename(raster_name)
            
        print('Creating shapefile', shapefile_name, "...")
        
        drv = ogr.GetDriverByName("ESRI Shapefile")
        ogr_out_shapefile = drv.CreateDataSource(shapefile_name)
        
        srs = None
        if gdal_raster.GetProjectionRef() != '':
            srs = osr.SpatialReference()
            srs.ImportFromWkt( gdal_raster.GetProjectionRef() )
            
        out_shapefle_name, extension = os.path.splitext(shapefile_name)
        shp_layername = os.path.basename(out_shapefle_name)
        ogr_out_shapefile_lyr = ogr_out_shapefile.CreateLayer(shp_layername, srs = srs )
        dst_fieldname = 'DN'
            
        fd = ogr.FieldDefn( dst_fieldname, ogr.OFTInteger )
        ogr_out_shapefile_lyr.CreateField( fd )
        dst_field = 0
        
        #polygonize raster
        prog_func = gdal.TermProgress
        result = gdal.Polygonize( gdal_raster_band, gdal_raster_mask, ogr_out_shapefile_lyr, 
                                  dst_field, options=[], callback=prog_func )
        print("Time to run convert raster to shapefile: %s" %
              datetime.datetime.utcnow()-time_start_convert)
            

if __name__ == "__main__":
    input_folder = "/Users/rdchlads/autorapid/Test_Case/n39w087"
    print ogr.GetDriverByName("ASCII")
    print ogr.GetDriverByName("Arc/Info ASCIIGRID")
    auto_mng = AutoRoute('/Users/rdchlads/autorapid/AutoRoute/source_code/autoroute',
                         stream_file=os.path.join(input_folder, "Flow_n39w087.asc"),
                         dem_file=os.path.join(input_folder, "dem_n39w087.asc"),
                         spatial_units="deg",
                         SHP_Out_File=os.path.join(input_folder,"tmp", "Flood_n39w087.tif"),
                         SHP_Out_Shapefile=os.path.join(input_folder,"tmp", "Flood_n39w087_test.shp"),
                         lu_raster=os.path.join(input_folder, "ar_lulc_clip.asc"),
                         LU_Manning_n=os.path.join(input_folder, "AR_Manning_n_for_NLCD_LOW.txt"),
                         X_Section_Dist=5000.0,
                         Q_Limit=1.01,
                         Use_Prev_D_4_XS=1,
                         PROPORTIONAL_FLOW=True,
                         Flow_Alpha=1.0,
                         STR_IS_M2=1000.0,
                         Gen_Dir_Dist=1,
                         Gen_Slope_Dist=1,
                         Thin_Non_PerpX=0,
                         Elim_Non_ConctX=1,
                         Degree_Manip=6.1,
                         Degree_Interval=1.5,
                         Low_Spot_Range=15,
                         Str_Limit_Val=1
                         )
                         
    auto_mng.run_autoroute()

    auto_mng.update_parameters(x_Section_dist=1200)       
    auto_mng.run_autoroute()
            
            
            
            