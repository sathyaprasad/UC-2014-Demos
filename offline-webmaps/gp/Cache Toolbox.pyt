#-------------------------------------------------------------------------------
# Name:        WebMap Cache
# Purpose:     Python toolbox to create cached versions of WebMaps and storing
#              the result as tpk on disk for offline usage
# Author:      Applications Prototype Lab, Esri
#
# Created:     2013/09/30
# Copyright:   (c) Esri 2013
# Licence:     CC-BY-SA
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import arcpy, urllib, urllib2, math, Queue, threading, random, json, os.path, subprocess

zoom_level_list = range(0,20)
lod_list = [[0, 591657527.591555,156543.033928],
              [1,295828763.795777,78271.5169639999],
              [2,147914381.897889,39135.7584820001],
              [3,73957190.948944,19567.8792409999],
              [4,36978595.474472,9783.93962049996],
              [5,18489297.737236,4891.96981024998],
              [6,9244648.868618,2445.98490512499],
              [7,4622324.434309,1222.99245256249],
              [8,2311162.217155,611.49622628138],
              [9,1155581.108577,305.748113140558],
              [10,577790.554289,152.874056570411],
              [11,288895.277144,76.4370282850732],
              [12,144447.638572,38.2185141425366],
              [13,72223.819286,19.1092570712683],
              [14,36111.909643,9.55462853563415],
              [15,18055.954822,4.77731426794937],
              [16,9027.977411,2.38865713397468],
              [17,4513.988705,1.19432856685505],
              [18,2256.994353,0.597164283559817],
              [19,1128.497176,0.298582141647617],
              [20,564.25,0.1493],
              [21,282.12,0.0746],
              [22,141.06,0.0373]]


# definition of cache levels for the data cache
cache_infos_name = 'conf.xml'
cache_infos_start = u"<?xml version='1.0' encoding='utf-8' ?> \
<CacheInfo xsi:type='typens:CacheInfo' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:typens='http://www.esri.com/schemas/ArcGIS/10.1'> \
  <TileCacheInfo xsi:type='typens:TileCacheInfo'> \
    <SpatialReference xsi:type='typens:ProjectedCoordinateSystem'> \
      <WKT>PROJCS[&quot;WGS_1984_Web_Mercator_Auxiliary_Sphere&quot;,GEOGCS[&quot;GCS_WGS_1984&quot;,DATUM[&quot;D_WGS_1984&quot;,SPHEROID[&quot;WGS_1984&quot;,6378137.0,298.257223563]],PRIMEM[&quot;Greenwich&quot;,0.0],UNIT[&quot;Degree&quot;,0.0174532925199433]],PROJECTION[&quot;Mercator_Auxiliary_Sphere&quot;],PARAMETER[&quot;False_Easting&quot;,0.0],PARAMETER[&quot;False_Northing&quot;,0.0],PARAMETER[&quot;Central_Meridian&quot;,0.0],PARAMETER[&quot;Standard_Parallel_1&quot;,0.0],PARAMETER[&quot;Auxiliary_Sphere_Type&quot;,0.0],UNIT[&quot;Meter&quot;,1.0],AUTHORITY[&quot;EPSG&quot;,3857]]</WKT> \
      <XOrigin>-20037700</XOrigin> \
      <YOrigin>-30241100</YOrigin> \
      <XYScale>148923141.92838538</XYScale> \
      <ZOrigin>-100000</ZOrigin> \
      <ZScale>10000</ZScale> \
      <MOrigin>-100000</MOrigin> \
      <MScale>10000</MScale> \
      <XYTolerance>0.001</XYTolerance> \
      <ZTolerance>0.001</ZTolerance> \
      <MTolerance>0.001</MTolerance> \
      <HighPrecision>true</HighPrecision> \
      <WKID>102100</WKID> \
      <LatestWKID>3857</LatestWKID> \
    </SpatialReference> \
    <TileOrigin xsi:type='typens:PointN'> \
      <X>-20037508.342787001</X> \
      <Y>20037508.342787001</Y> \
    </TileOrigin> \
    <TileCols>256</TileCols> \
    <TileRows>256</TileRows> \
    <DPI>96</DPI> \
    <PreciseDPI>96</PreciseDPI> \
    <LODInfos xsi:type='typens:ArrayOfLODInfo'>"
LODInfo_level = u"<LODInfo xsi:type='typens:LODInfo'> \
        <LevelID>{0}</LevelID> \
        <Scale>{1}</Scale> \
        <Resolution>{2}</Resolution> \
      </LODInfo>"
cache_infos_end = u"</LODInfos> \
  </TileCacheInfo> \
  <TileImageInfo xsi:type='typens:TileImageInfo'> \
    <CacheTileFormat>JPEG</CacheTileFormat> \
    <CompressionQuality>75</CompressionQuality> \
    <Antialiasing>false</Antialiasing> \
  </TileImageInfo> \
  <CacheStorageInfo xsi:type='typens:CacheStorageInfo'> \
    <StorageFormat>esriMapCacheStorageModeExploded</StorageFormat> \
  </CacheStorageInfo> \
</CacheInfo>"

#the conf.cdi file
c_name = 'conf.cdi'
bounding_box = '<XMin>{0}</XMin><YMin>{1}</YMin><XMax>{2}</XMax><YMax>{3}</YMax>'

cache_reference_info = "<?xml version='1.0' encoding='utf-8' ?><EnvelopeN xsi:type='typens:EnvelopeN' \
xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xs='http://www.w3.org/2001/XMLSchema' \
xmlns:typens='http://www.esri.com/schemas/ArcGIS/10.1'>REPLACE_BOUNDS \
<SpatialReference xsi:type='typens:ProjectedCoordinateSystem'><WKT>PROJCS[&quot;WGS_1984_Web_Mercator_Auxiliary_Sphere&quot;\
,GEOGCS[&quot;GCS_WGS_1984&quot;,DATUM[&quot;D_WGS_1984&quot;,SPHEROID[&quot;WGS_1984&quot;,6378137.0,298.257223563]],\
PRIMEM[&quot;Greenwich&quot;,0.0],UNIT[&quot;Degree&quot;,0.0174532925199433]],PROJECTION[&quot;Mercator_Auxiliary_Sphere&quot;]\
,PARAMETER[&quot;False_Easting&quot;,0.0],PARAMETER[&quot;False_Northing&quot;,0.0],PARAMETER[&quot;Central_Meridian&quot;,0.0]\
,PARAMETER[&quot;Standard_Parallel_1&quot;,0.0],PARAMETER[&quot;Auxiliary_Sphere_Type&quot;,0.0],UNIT[&quot;Meter&quot;,1.0],\
AUTHORITY[&quot;EPSG&quot;,3857]]</WKT><XOrigin>-20037700</XOrigin><YOrigin>-30241100</YOrigin>\
<XYScale>148923141.92838538</XYScale><ZOrigin>-100000</ZOrigin><ZScale>10000</ZScale><MOrigin>-100000</MOrigin>\
<MScale>10000</MScale><XYTolerance>0.001</XYTolerance><ZTolerance>0.001</ZTolerance>\
<MTolerance>0.001</MTolerance><HighPrecision>true</HighPrecision><WKID>102100</WKID>\
<LatestWKID>3857</LatestWKID></SpatialReference></EnvelopeN>"



level_prefix = 'L'
row_prefix = 'R'
column_prefix = 'C'
instance_list = ['a','b','c','d']

def deg2num(lat_deg, lon_deg, zoom):
    """Provided geographic coordinates in WGS84 and the zoom level the function will
    return matching tile numbers for a Google/Bing/ArcGIS Online tiling scheme."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def num2bounds(xtile, ytile, zoom):
    [ymax, xmin] = num2deg(xtile, ytile, zoom)
    [ymin, xmax] = num2deg(xtile + 1, ytile + 1, zoom)
    return (xmin, ymin, xmax, ymax)

def getScale(zoom):
    baseScale = 591657527.591555
    zoom_int = int(zoom)
    if zoom_int == 0:
        return baseScale

    scale = baseScale
    for index in range(1,zoom_int + 1):
        scale = scale / 2

    return scale

def getResolution(zoom):
    baseResolution = 156543.03392800014
    zoom_int = int(zoom)
    if (zoom_int) == 0:
        return baseResolution

    resolution = baseResolution
    for index in range(1,zoom_int + 1):
        resolution = resolution / 2
    return resolution


class TileGetSaveThread(threading.Thread):
    """Threaded get tile and save to file"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            #get the tile URL and tile name from queue
            tile_data_file = self.queue.get()

            # save the download as an file into the cache structure
            try:
                data = urllib.urlencode(tile_data_file[1])
                request = urllib2.Request(tile_data_file[0], data)
                response = urllib2.urlopen(request)

                print_response = json.loads(response.read())

                response = urllib2.urlopen(print_response['results'][0]['value']['url'])

                current_tile = open(tile_data_file[2],'wb')
                current_tile.write(response.read())

            except:
                pass
            finally:
                if current_tile:
                    current_tile.close()

            #signals to queue job is done
            self.queue.task_done()

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Caching Toolbox"
        self.alias = "apl"

        # List of tool classes associated with this toolbox
        self.tools = [CreateWebMapCache]


class CreateWebMapCache(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create WebMap Cache"
        self.description = "Creates a local tpk from a WebMap"
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        export_url_parameter = arcpy.Parameter(
            displayName="Export Task URL",
            name="in_PrintURL",
            datatype="String",
            parameterType="Required",
            direction="Input")
        export_url_parameter.value = u"https://utility.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute"

        starting_LOD_parameter = arcpy.Parameter(
            displayName="Current Level of Detail",
		    name="in_startingLOD",
            datatype="Long",
            parameterType="Required",
            direction="Input")
        starting_LOD_parameter.filter.type = "Range"
        starting_LOD_parameter.filter.list = [0,19]
        starting_LOD_parameter.value = 0

        number_of_levels_parameter = arcpy.Parameter(
            displayName="Number of Level of Details",
            name="in_number_of_lods",
            datatype="Long",
            parameterType="Required",
            direction="Input")
        number_of_levels_parameter.value = 5

        tile_format_parameter = arcpy.Parameter(
            displayName="Tile Format",
            name="in_tileformat",
            datatype="String",
            parameterType="Required",
            direction="Input")
        tile_format_parameter.value = "jpg"
        tile_format_parameter.filter.type = "ValueList"
        tile_format_parameter.filter.list = ["jpg", "png8", "png32"]

        request_extent_parameter = arcpy.Parameter(
            displayName="Request Extent",
            name="in_requestExtent",
            datatype="Extent",
            parameterType="Required",
            direction="Input")

        webmap_json_parameter = arcpy.Parameter(
            displayName="WebMap (JSON)",
            name="in_webmap_json",
            datatype="String",
            parameterType="Required",
            direction="Input")

        output_tpk_parameter = arcpy.Parameter(
            displayName="Output TPK Location",
            name="out_tpk_location",
            datatype="File",
            parameterType="Required",
            direction="Output")

        params = [export_url_parameter, starting_LOD_parameter, number_of_levels_parameter, tile_format_parameter, request_extent_parameter, webmap_json_parameter, output_tpk_parameter]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        tileCounter = 0
        # number of LODs to request starting from the starting with the LOD below
        LODs2request = 5
        max_available_level = 19
        tile_format = "jpg"

        print_task_url = parameters[0].valueAsText
        starting_LOD = int(parameters[1].valueAsText)

        LODs2request = int(parameters[2].valueAsText)
        tile_format = parameters[3].valueAsText

        request_extent = arcpy.Extent(*parameters[4].valueAsText.split(' '))

        # TODO: not sure how to incorporate different spatial reference with the extent object
        # -- we might have to switch to one of geometry classes to handle this situation
        wgs84extent = arcpy.Multipoint(arcpy.Array([arcpy.Point(request_extent.XMin, request_extent.YMin), arcpy.Point(request_extent.XMax, request_extent.YMax)]), arcpy.SpatialReference(4326)).extent
        wm_request_extent = arcpy.Multipoint(arcpy.Array([arcpy.Point(request_extent.XMin, request_extent.YMin), arcpy.Point(request_extent.XMax, request_extent.YMax)]), arcpy.SpatialReference(4326)).extent.projectAs(arcpy.SpatialReference(3857))
        #return

        # load the webmap json into a python dictionary
        webMap_dictionary = json.loads(parameters[5].valueAsText)

        # retrieve output location for the tpk file
        tpk_store_location = parameters[6].valueAsText

        # we'll use the scratch folder to assemble and store our cache
        cache_storage_location = arcpy.env.scratchFolder
        arcpy.AddMessage(cache_storage_location)

        # set the name of the data cache, which is the concatenation of the scratch folder and the cache name
        # assume the cache name to be 'OfflineWebMap'
        cacheName = 'OfflineWebMap'
        #arcpy.SetParameterAsText(6, arcpy.os.path.join(workingFolder, cacheName))

        # store the start and end tile coordinates and the zoom level in an array
        # describing each level of detail (LOD)
        lodes = []
        # assemble a list containing the UL and LR grid coordinates and the zoom level
        for zoom_level in range(starting_LOD, starting_LOD + LODs2request):
            # check that we not requesting details beyond available levels
            if zoom_level <= max_available_level:
                lodes.append([deg2num(request_extent.YMax,request_extent.XMin,zoom_level),deg2num(request_extent.YMin,request_extent.XMax,zoom_level),zoom_level])

        # create the directory to store the data cache
        target_cache_dir = arcpy.os.path.join(cache_storage_location,cacheName)
        try:
            arcpy.os.makedirs(target_cache_dir)
        except:
            pass

        # persist the conf.cdi and conf.xml
        # those are file describing the entities of the data cache
        bounding_insert = bounding_box.format(wm_request_extent.XMin, wm_request_extent.YMin, wm_request_extent.XMax, wm_request_extent.YMax)
        content = cache_reference_info.replace('REPLACE_BOUNDS', bounding_insert)

        conf_xml_file_name = arcpy.os.path.join(target_cache_dir, cache_infos_name)
        conf_xml_file = open(conf_xml_file_name,'w')
        # write the start of the lod description file
        conf_xml_file.write(cache_infos_start)
        for zoom_level in range(0, 20):
            # check that we not requesting details beyond available levels
            if zoom_level <= max_available_level:
                # write the required LOD Info level with level, scale, resolution filled in
                conf_xml_file.write(LODInfo_level.format(lod_list[zoom_level][0],lod_list[zoom_level][1],lod_list[zoom_level][2]))

        # finishing the lod description
        conf_xml_file.write(cache_infos_end)
        conf_xml_file.close()

        conf_sdi_file_name = arcpy.os.path.join(target_cache_dir,c_name)
        conf_sdi_file = open(conf_sdi_file_name,'w')
        conf_sdi_file.write(content)
        conf_sdi_file.close()

        # create the overall sublayer containing all the tiles
        target_cache_dir_all = arcpy.os.path.join(target_cache_dir, '_alllayers')
        try:
            arcpy.os.mkdir(target_cache_dir_all)
        except:
            pass

        # count all the tiles that we are expecting to download, we'll use this information
        # to drive the progressbar
        download_count = 0
        for zoom_level_index in range(len(lodes)):
            rows = len(range(lodes[zoom_level_index][0][1],lodes[zoom_level_index][1][1] + 1))
            columns = len(range(lodes[zoom_level_index][0][0],lodes[zoom_level_index][1][0] + 1))
            download_count = download_count + (rows * columns)

        # increase the counter by 1% increments
        step = download_count / 100
        if (step == 0):
            step = 1

        # set the label for the progress indicator as well as min and max values
        arcpy.SetProgressor('default','Downloading map tiles....', 0, download_count, step)

        tile_counter = 0

        # let's set up a queue for the tile requests
        queue = Queue.Queue()

        # create a thread pool of 6 and pass them the queue instance
        for i in range(6):
            fetchThread = TileGetSaveThread(queue)
            fetchThread.setDaemon(True)
            fetchThread.start()

        # for each of the zoom level
        for zoom_level_index in range(len(lodes)):
            arcpy.AddMessage('Downloading content for level ' + str(lodes[zoom_level_index][2]) + '...')
            # create the level directory
            zoom_level_dir = arcpy.os.path.join(target_cache_dir_all, level_prefix + str(lodes[zoom_level_index][2]).zfill(2))
            try:
                arcpy.os.mkdir(zoom_level_dir)
            except:
                pass

            # for each row in the zoom level
            for row_index in range(lodes[zoom_level_index][0][1],lodes[zoom_level_index][1][1] + 1):
                # assemble the row name
                # which is row number expressed as hex  and padded to eight digits
                row_dir_name = row_prefix + hex(row_index).replace('0x','').zfill(8)
                row_level_dir = arcpy.os.path.join(zoom_level_dir, row_dir_name)
                try:
                    arcpy.os.mkdir(row_level_dir)
                except:
                    pass

                # for each column now request the tile and save it by the new name
                for column_index in range(lodes[zoom_level_index][0][0],lodes[zoom_level_index][1][0] + 1):

                    # assemble the column tile name
                    # which is column number expressed as hex  nd padded to eight digits
                    tile_name = column_prefix + hex(column_index).replace('0x','').zfill(8)
                    tile_save_filename = arcpy.os.path.join(row_level_dir,tile_name)

                    # replace the zoom level, row and column number in the TMS request
                    request_data = {}

                    # replace the request extent to match the current tile
                    tile_web_map_json = webMap_dictionary
                    [tile_xmin, tile_ymin, tile_xmax, tile_ymax]= num2bounds(column_index, row_index, lodes[zoom_level_index][2])
                    tile_extent = {'xmin': tile_xmin, 'ymin': tile_ymin, 'xmax':tile_xmax, 'ymax':tile_ymax, 'spatialreference': {'wkid':4326}}
                    tile_web_map_json['mapOptions']['extent'] = tile_extent
                    tile_web_map_json['mapOptions']['scale'] = lod_list[lodes[zoom_level_index][2]][1]
                    request_data['Web_Map_as_JSON'] = json.dumps(tile_web_map_json)
                    request_data['Format'] = tile_format
                    request_data['Layout_Template'] = 'MAP_ONLY'
                    request_data['f'] = 'json'
                    # have the file extension match the requested format
                    tile_save_filename = tile_save_filename + '.' + tile_format[:3]


                    # place the download url and the file name into the request queue
                    queue.put([print_task_url, request_data, tile_save_filename])

        # wait until all threads are done with all the items on the queue
        queue.join()

        # reset the progress bar indicator
        arcpy.ResetProgressor()

        # launch an external python process to the generation of the tpk
        # uncomment those lines after the gp has been published to the server
        #package_script_location = os.path.join(os.path.dirname(__file__), "tpk_package.py")
        #arcpy.AddMessage(str(['C:\\Python27\\ArcGISx6410.2\\python.exe', package_script_location, target_cache_dir, tpk_store_location]))
        #p = subprocess.Popen(['C:\\Python27\\ArcGISx6410.2\\python.exe', package_script_location, target_cache_dir, tpk_store_location])
        #p.wait()
        arcpy.ExportTileCache_management(target_cache_dir, os.path.dirname(tpk_store_location), os.path.basename(tpk_store_location), 'TILE_PACKAGE', 'COMPACT')

        # delete the intermediate downloaded raster cache
        arcpy.Delete_management(target_cache_dir)

        return
