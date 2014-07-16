#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Thomas
#
# Created:     08/10/2013
# Copyright:   (c) Thomas 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import arcpy, os, sys

target_cache_dir = sys.argv[1]
tpk_store_location = sys.argv[2]

print(target_cache_dir)
print(tpk_store_location)
try:

    # package the exploded cache into the final tpk
    arcpy.ExportTileCache_management(target_cache_dir, os.path.dirname(tpk_store_location), os.path.basename(tpk_store_location), 'TILE_PACKAGE', 'COMPACT')
except:
    print "Unexpected error:", sys.exc_info()[0]
    print "Unexpected error:", sys.exc_info()[1]