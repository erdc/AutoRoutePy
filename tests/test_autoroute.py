from filecmp import cmp as fcmp
from nose.tools import raises, ok_
import os
from shutil import copy


#local import
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from AutoRoutePy.autoroute import AutoRoute

@raises(Exception)
def test_generate_autoroute_input_file_invalid():
    """
    Checks AutoRoute input file generation with invalid input
    """
    main_tests_folder = os.path.dirname(os.path.abspath(__file__))
    
    ouptut_data_path = os.path.join(main_tests_folder, 'output')

    print "TEST 1: GENERATE INPUT FILE WITH INVALID INPUTS"
    auto_mng_gen = AutoRoute("autoroute_exe_path_dummy",
                             stream_file="streamflow_raster.tif",
                             dem_file="elevation.tif",
                             shp_out_file="right_here.shp",
                             frank="fake",
                             x_section_dist=5000.0,
                             str_limit_val=1,
                             q_limit=1.01,
                             man_n=0.035,
                             flow_alpha=1,
                             degree_interval=1.5
                             )

    generated_input_file = os.path.join(ouptut_data_path, 
                                        "AUTOROUTE_INPUT_FILE-GENERATE_INVALID.txt")
    auto_mng_gen.generate_input_file(generated_input_file)
    try:
        os.remove(generated_input_file)
    except OSError:
        pass

def test_generate_autoroute_input_file():
    """
    Checks AutoRoute input file generation with valid input
    """
    main_tests_folder = os.path.dirname(os.path.abspath(__file__))
    
    original_data_path = os.path.join(main_tests_folder, 'original')
    ouptut_data_path = os.path.join(main_tests_folder, 'output')

    print "TEST 2: GENERATE INPUT FILE"
    auto_mng_gen = AutoRoute("autoroute_exe_path_dummy",
                             stream_file="streamflow_raster.tif",
                             dem_file="elevation.tif",
                             shp_out_file="right_here.shp",
                             x_section_dist=5000.0,
                             thin_non_perpx=0,
                             degree_manip=3.1,
                             elim_non_conctx=1,
                             low_spot_range=15,
                             use_prev_d_4_xs=1,
                             gen_dir_dist=1,
                             gen_slope_dist=1,
                             spatial_units="deg",
                             str_is_m2=1000.0,
                             proportional_flow=True,
                             str_limit_val=1,
                             q_limit=1.01,
                             man_n=0.035,
                             flow_alpha=1,
                             degree_interval=1.5
                             )

    generated_input_file = os.path.join(ouptut_data_path, 
                                        "AUTOROUTE_INPUT_FILE-GENERATE.txt")
    auto_mng_gen.generate_input_file(generated_input_file)
    generated_input_file_solution = os.path.join(original_data_path, 
                                                 "AUTOROUTE_INPUT_FILE-GENERATE_SOLUTION.txt")
    ok_(fcmp(generated_input_file, generated_input_file_solution))
    
    try:
        os.remove(generated_input_file)
    except OSError:
        pass

@raises(Exception)
def test_update_autoroute_input_file_invalid():
    """
    Checks AutoRoute input file update with invalid input
    """
    main_tests_folder = os.path.dirname(os.path.abspath(__file__))
    
    original_data_path = os.path.join(main_tests_folder, 'original')
    output_data_path = os.path.join(main_tests_folder, 'output')

    print "TEST 3: UPDATE INPUT FILE WITH FAKE INPUTS"
    auto_mng_fake = AutoRoute("autoroute_exe_path_dummy",
                             stream_file=os.path.join(original_data_path, "streamflow_raster.tif"),
                             dem_file=os.path.join(output_data_path, "elevation.tif"),
                             shp_out_file="right_here.shp",
                             )

    original_fake_input_file = os.path.join(output_data_path, 
                                            "AUTOROUTE_INPUT_FILE-INVALID_INPUTS.txt")
    out_fake_input_file = os.path.join(output_data_path, 
                                       "AUTOROUTE_INPUT_FILE-INVALID_INPUTS.txt")
    copy(original_fake_input_file, out_fake_input_file)
    auto_mng_fake.update_input_file(out_fake_input_file)

    try:
        os.remove(out_fake_input_file)
    except OSError:
        pass

def test_update_autoroute_input_file():
    """
    Checks AutoRoute input file generation with valid input
    """
    main_tests_folder = os.path.dirname(os.path.abspath(__file__))
    
    original_data_path = os.path.join(main_tests_folder, 'original')
    output_data_path = os.path.join(main_tests_folder, 'output')

    print "TEST 4: UPDATE VARIABLES IN FILE"
    auto_mng_var = AutoRoute("autoroute_exe_path_dummy",
                             stream_file="streamflow_raster.tif",
                             dem_file="elevation.tif",
                             shp_out_file="right_here.shp",
                             low_spot_range=35,
                             use_prev_d_4_xs=0,
                             gen_dir_dist=0,
                             gen_slope_dist=0,
                             spatial_units="m",
                             str_is_m2=1002.4,
                             proportional_flow=False,
                             str_limit_val=2
                             )

    original_var_input_file = os.path.join(original_data_path, 
                                           "AUTOROUTE_INPUT_FILE-UPDATE_VAR.txt")
    out_var_input_file = os.path.join(output_data_path, 
                                      "AUTOROUTE_INPUT_FILE-UPDATE_VAR.txt")
    copy(original_var_input_file, out_var_input_file)
    auto_mng_var.update_input_file(out_var_input_file)
    updated_input_file_solution = os.path.join(original_data_path, 
                                               "AUTOROUTE_INPUT_FILE-UPDATE_VAR_SOLUTION.txt")
    ok_(fcmp(out_var_input_file, updated_input_file_solution))

    try:
        os.remove(out_var_input_file)
    except OSError:
        pass
        
if __name__ == '__main__':
    import nose
    nose.main()