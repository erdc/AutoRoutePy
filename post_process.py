# -*- coding: utf-8 -*-
from glob import glob
import os
from osgeo import ogr
from shutil import copy

#------------------------------------------------------------------------------
#AutoRoute Post Processing Functions
#------------------------------------------------------------------------------

def merge_shapefiles(directory, out_shapefile_name, remove_old=False):
    """
    Merges all shapefiles in a directory
    """
    print "Merging Shapefiles ..."
    out_driver = ogr.GetDriverByName( 'ESRI Shapefile' )
    if os.path.exists(out_shapefile_name):
        out_driver.DeleteDataSource(out_shapefile_name)
    out_ds = out_driver.CreateDataSource(out_shapefile_name)
    out_layer = out_ds.CreateLayer(out_shapefile_name, geom_type=ogr.wkbPolygon)
    
    #create projection file
    projection_file = glob(os.path.join(directory, "*.prj"))[0]
    copy(projection_file, "%s.prj" % os.path.splitext(out_shapefile_name)[0])
    
    fileList = glob(os.path.join(directory, "*.shp"))
    
    for file_path in fileList:
        ds = ogr.Open(file_path)
        lyr = ds.GetLayer()
        for feat in lyr:
            out_feat = ogr.Feature(out_layer.GetLayerDefn())
            out_feat.SetGeometry(feat.GetGeometryRef().Clone())
            out_layer.CreateFeature(out_feat)
            out_layer.SyncToDisk()

        if remove_old:
            all_assocaited_files = glob("%s*" % os.path.splitext(file_path)[0])
            for associated_file in  all_assocaited_files:
                try:
                    os.remove(associated_file)
                except OSError:
                    pass
                
def rename_shapefiles(directory, out_shapefile_basename, startswith=""):
    """
    Renames all shapefiles in a directory
    """

    print "Renaming Shapefiles ..."
    fileList = glob(os.path.join(directory, "%s*.shp" % startswith))
    for file_name in fileList:
        extension = os.path.splitext(file_name)[1]
        os.rename(file_name, os.path.join(directory, "%s%s" % (out_shapefile_basename, extension)))
        
            