 /*
    This code shows an example of using the HTML5 Gamepad API with the ArcGIS Javascript API. This demo works on the newest version of Chrome (I used version 35.)
 */

 var hasGP = false;
 var mymap = null;
 var mapResponse = null;
 var helpHidden = true;
 var isButtonBusy = false;
 var showingLegend = false;
 var showingTitleBar = true;
 var originalHelpText = '';
 var changedOriginalText = true;
 var descriptionShown = false;

// use these defaults if there is no group brought back
 var webmapgallery = ['d94dcdbe78e141c2b2d3a91d5ca8b9c9', '4778fee6371d4e83a22786029f30c7e1', 'c63cdcbbba034b62a2f3becac021b0a8', 'ef5920f160bd4239bdeb1348de3a3156',
     '8a567ebac15748d39a747649a2e86cf4', '2618187b305f4eafbae8fd6eb52afc76'
 ];

 var basemapTypes = ['streets', 'hybrid', 'topo', 'gray', 'oceans', 'national-geographic', 'osm'];
 var basemapIndex = 0;
 var bookmarkIndex = 0;
 var mapIndex = 0;
 var legendDijit;
 var overviewMapDijit;
 var isBusy = false;

// using the dojo AMD pattern
 require([
     "dojo/ready",
     "esri/map",
     'esri/dijit/Legend',
     "esri/dijit/OverviewMap",
     "esri/arcgis/Portal",
     "esri/urlUtils",
     "esri/arcgis/utils"
 ], function(ready,
     Map,
     Legend,
     OverviewMap,
     Portal,
     urlUtils,
     arcgisUtils) {

     ready(function() {

         'use strict';
         //get webmap id
         var webmapid = 'd94dcdbe78e141c2b2d3a91d5ca8b9c9';
         var groupid = '46b23d6bfae34260a61b1ea4e266b4a4';

          var defaultGeometryServerUrl = document.location.protocol + "//utility.arcgisonline.com/arcgis/rest/services/Geometry/GeometryServer";
          esri.config.defaults.geometryService = new esri.tasks.GeometryService(defaultGeometryServerUrl);

          // can also get groups dynamically from the url
         var hrefObject = esri.urlToObject(document.location.href);
         if (hrefObject.query && hrefObject.query.webmap) {
             webmapid = hrefObject.query.webmap;
         }

         if (hrefObject.query && hrefObject.query.groupid) {
             groupid = hrefObject.query.groupid;
         }

         if (groupid) {
             var portal = new esri.arcgis.Portal('http://www.arcgis.com');
             portal.on("load", function() {
                 var params = {
                     q: 'group:' + groupid + " AND " + "type:Web Map"
                 };
                 portal.queryItems(params).then(function(items) {
                     var results = items.results;
                     if (results.length > 0) {
                         webmapgallery = [];
                         for (var i = results.length - 1; i >= 0; i--) {
                             var result = results[i];
                             if (result.type == "Web Map") {
                                 webmapgallery.push(result.id);
                             }
                         }
                         loadMap(webmapgallery[0]);
                     } else {
                         alert("Sorry, no webmaps are available in this group. Loading a default map.");
                         loadMap(webmapid);
                     }
                 }, function(err) {
                     console.log(err);
                     alert("Sorry, could not load the group items. Loading a default map.");
                     loadMap(webmapid);
                 });
             });

         } else {
             //add the map
             loadMap(webmapid);
         }
     });

 });


 function loadMap(webmapid) {
     require(['dojo/_base/array'], function(arrayUtils) {
         dojo.byId('help-text').innerHTML = 'Press \'A\' to get help.';
         if (mymap) {
             mymap.destroy();
             dojo.byId('help-text').style.display = 'none';
             dojo.byId('legend-div').style.display = "none";
             basemapIndex = 0;
             bookmarkIndex = 0;
             if (overviewMapDijit) overviewMapDijit.destroy();
             dojo.byId('help-text').innerHTML = '';
             dojo.byId("title").innerHTML = "Loading ...";
         } else {
            dojo.byId('help-text').style.display = 'inline-block';
         }

         esri.arcgis.utils.createMap(webmapid, "mapdiv").then(function(response) {

             dojo.byId("title").innerHTML = "<h3>" + response.itemInfo.item.title + "</h3>";
             dojo.byId('description').innerHTML = response.itemInfo.item.description;
             mymap = response.map;

             mymap.hideZoomSlider();
             mapResponse = response;
             mymap.initialExtent = mymap.extent;

             var legendLayers = esri.arcgis.utils.getLegendLayers(response);

             //set basemap layerids
             if (mymap.basemapLayerIds && mymap.basemapLayerIds.length > 0) {
                 //good to go
             } else {
                 mymap.basemapLayerIds = [];
                 for (var i = 0; i < mapResponse.itemInfo.itemData.baseMap.baseMapLayers.length; i++) {
                     mymap.basemapLayerIds.push(mapResponse.itemInfo.itemData.baseMap.baseMapLayers[i].id);
                 };
             }

             isBusy = false;
             changedOriginalText = true;             

             if (legendDijit) {
                legendDijit.layerInfos = legendLayers;
                legendDijit.refresh();
             } else {
                 legendDijit = new esri.dijit.Legend({
                     map: mymap,
                     layerInfos: legendLayers
                 }, 'legend-div');
                 legendDijit.startup();
             }

             overviewMapDijit = new esri.dijit.OverviewMap({
                 map: mymap,
                 attachTo: "bottom-left",
                 color: " #D84E13",
                 opacity: .40
             });

             overviewMapDijit.startup();
             overviewMapDijit.show();

             hasBookmarks();

             initializeGamePad();
         }, function(err) {
             console.log(err);
             isBusy = false;
         });
     });
 }

// see if any gamepads are connected -- we're only allowing one at a time in this demo.
 function canGame() {
     return "getGamepads" in navigator;
 }

 window.requestAnimFrame = (function() {
     return window.requestAnimationFrame ||
         window.webkitRequestAnimationFrame ||
         window.mozRequestAnimationFrame ||
         function(callback) {
             window.setTimeout(callback, 1000 / 60);
         };
 })();

 function initializeGamePad() {
     if (mymap == null) {
         alert("map is null");
         return;
     }

     if (hasGP) return;
     var timer = null;

     // add listeners for when the gamepad is connected or disconnected
     window.addEventListener('gamepadconnected', function() {
         hasGP = true;
         dojo.byId('connect-status').className = 'connected';
         timer = window.setInterval(checkGamepad, 100);
     });
     window.addEventListener('gamepaddisconnected', function() {
         window.clearInterval(timer);
         dojo.byId('connect-status').className = 'disconnected';
     });

     //setup an interval for Chrome
     var checkGP = window.setInterval(function() {
         if (navigator.getGamepads()[0]) {
             if (!hasGP) {
                 dojo.byId('connect-status').className = 'connected';
                 timer = window.setInterval(checkGamepad, 100);
             }
             window.clearInterval(checkGP);
         } else {
             dojo.byId('connect-status').className = 'disconnected';
         }
     }, 500);
 }

 // we call this function on an interval (not continuously) so we don't overload (otherwise, one button press might register as 4 or 5 presses)
 function checkGamepad() {
     // we only want one gamepad controlling the map
     var gamepad = navigator.getGamepads()[0];
     if (canGame()) {
         pollButtons(gamepad);
         checkAxes(gamepad);
     }
 }

 // loop through the buttons periodically and if any are pressed, perform their associated action.
 function pollButtons(gamepad) {
     for (var i = 0; i < gamepad.buttons.length; i++) {
         if (gamepad.buttons[i].pressed) {
             var buttonName = '';
             if (i < 12) {
                 if (isButtonBusy) return;
                 isButtonBusy = true;
                 switch (i) {
                     case 0:
                         buttonName = "A";
                         toggleHelp();
                         break;
                     case 1:
                         buttonName = "B";
                         displayBookmark();
                         break;
                     case 2:
                         buttonName = "X";
                         mapAction('switchBasemap');
                         break;
                     case 3:
                         buttonName = "Y";
                         toggleLegend();
                         break;
                     case 4:
                         buttonName = "Left top trigger";
                         mapAction('previousMap');
                         break;
                     case 5:
                         buttonName = "Right top trigger";
                         mapAction('nextMap');
                         break;
                     case 6:
                         buttonName = "Left bottom trigger";
                         mapAction('zoomout');
                         break;
                     case 7:
                         buttonName = "Right bottom trigger";
                         mapAction('zoomin');
                         break;
                     case 8:
                         buttonName = "Back";
                         mapAction('reset');
                         break;
                     case 9:
                         buttonName = "Start";
                         toggleDescription();
                         break;
                     case 10:
                         buttonName = "A";
                         break;
                     case 11:
                         buttonName = "A";
                         break;
                     default:
                         break;
                 }

                 setTimeout(function() {
                     isButtonBusy = false;
                 }, 200);

             } else {
                 switch (i) {
                     case 12:
                         buttonName = "Up";
                         mapAction('panup');
                         break;
                     case 13:
                         buttonName = "Down";
                         mapAction('pandown');
                         break;
                     case 14:
                         buttonName = "Left";
                         mapAction('panleft');
                         break;
                     case 15:
                         buttonName = "Right";
                         mapAction('panright');
                         break;
                     default:
                         break;
                 }
             }
         }
     }
 }

 function toggleTitleBar() {
     if (showingTitleBar) {
         dojo.byId('header').style.display = "none";
     } else {
         dojo.byId('header').style.display = "inline-block";
     }
     showingTitleBar = !showingTitleBar;
 }

 function toggleLegend() {
     if (showingLegend) {
         dojo.byId('legend-div').style.display = "none";
     } else {
         dojo.byId('legend-div').style.display = "inline-block";
     }
     showingLegend = !showingLegend;
 }

 function hasBookmarks() {
     // if there are any...     
     var bookmarks = mapResponse.itemInfo.itemData.bookmarks;
     if (bookmarks && bookmarks.length > 0) {
         var pluralSuffix = bookmarks.length > 1 ? 's' : '';
         dojo.byId('help-text').style.display = 'inline-block';
         var bookmarkText = bookmarks.length + ' Bookmark' + pluralSuffix + ' available! Press B to get started.';
         dojo.byId('help-text').innerHTML = bookmarkText;
     }
 }

 function displayBookmark() {
     var bookmarks = mapResponse.itemInfo.itemData.bookmarks;
     dojo.byId('help-text').style.display = 'inline-block';
     if (bookmarks && bookmarks.length > 0) {
         // set this to do.
         if (bookmarkIndex > bookmarks.length - 1) {
             bookmarkIndex = 0;
             var pluralSuffix = bookmarks.length > 1 ? 's' : '';
             var bookmarkText = bookmarks.length + ' Bookmark' + pluralSuffix + ' available! Press B to get started.';
             dojo.byId('help-text').innerHTML = bookmarkText;
             mymap.setExtent(mymap.initialExtent);
         } else {
             // set extent
             dojo.byId('help-text').innerHTML = "Showing Bookmark " + (bookmarkIndex + 1) + ' of ' + bookmarks.length;
             var newExtent = new esri.geometry.Extent(bookmarks[bookmarkIndex].extent);
             mymap.setExtent(newExtent, true);
             bookmarkIndex++;
         }
     }
     else {
        dojo.byId('help-text').innerHTML = 'No bookmarks to show.';
     }
 }

 function toggleDescription() {
    if(descriptionShown) {
        dojo.byId('description-container').style.display = 'none';
    }
    else {
        dojo.byId('description-container').style.display = 'inline-block';   
    }
    descriptionShown = !descriptionShown;
 }

 function toggleHelp() {
     if (helpHidden) {
         dojo.byId('help-pics').style.display = 'block';
     } else {
         dojo.byId('help-pics').style.display = 'none';
     }
     helpHidden = !helpHidden;
 }

 function checkAxes(gamepad) {
     var axesActions = {
         leftZoomIn: false,
         leftZoomOut: false,
         rightZoomIn: false,
         rightZoomOut: false,

         panUp: false,
         panDown: false,
         panLeft: false,
         panRight: false,
         panUpLeft: false,
         panUpRight: false,
         panDownLeft: false,
         panDownRight: false
     };

     for (var i = 0; i < gamepad.axes.length; i += 2) {
         var x = gamepad.axes[i];
         var y = gamepad.axes[i + 1];

         var diffNeg = -0.4;
         var diffPos = 0.4;

         // check the right analog stick
         if (i > 1) {
             if (x > diffPos && y > diffPos) {
                 axesActions.rightZoomIn = true;
             } else if (x < diffNeg && y < diffNeg) {
                 axesActions.rightZoomOut = true;
             }
         }
         // left analog stick
         else {
             if (x > diffPos && y > diffPos) {
                 axesActions.panDownRight = true;
             } else if (x < diffNeg && y < diffNeg) {
                 axesActions.panUpLeft = true;
             } else if (x > diffPos && y < diffNeg) {
                 // account for each of the 
                 axesActions.panUpRight = true;
             } else if (x < diffNeg && y > diffPos) {
                 axesActions.panDownLeft = true;
             } else if (x < diffNeg && y < diffPos && y > diffNeg) {
                 axesActions.panLeft = true;
             } else if (x > diffPos && y < diffPos && y > diffNeg) {
                 axesActions.panRight = true;
             } else if (y > diffPos && x < diffPos && x > diffNeg) {
                 axesActions.panDown = true;
             } else if (y < diffNeg && x < diffPos && x > diffNeg) {
                 axesActions.panUp = true;
             }
         }
     }

     checkAxesActions(axesActions);
 }

 function checkAxesActions(axesActions) {
     if (axesActions.panDownRight) {
         mapAction('pandownright');
     } else if (axesActions.panUpRight) {
         mapAction('panupright');
     } else if (axesActions.panDownLeft) {
         mapAction('pandownleft');
     } else if (axesActions.panUpLeft) {
         mapAction('panupleft');
     } else if (axesActions.panLeft) {
         mapAction('panleft');
     } else if (axesActions.panRight) {
         mapAction('panright');
     } else if (axesActions.panUp) {
         mapAction('panup');
     } else if (axesActions.panDown) {
         mapAction('pandown');
     }
 }

 function mapAction(type) {

     if (isBusy) return;

     switch (type) {
         case 'zoomin':
             setPanZoomHelpText();
             mymap.setLevel(mymap.getLevel() + 1);
             break;
         case 'zoomout':
             setPanZoomHelpText();
             mymap.setLevel(mymap.getLevel() - 1);
             break;
         case 'panup':
             setPanZoomHelpText();
             mymap.panUp();
             break;
         case 'pandown':
             setPanZoomHelpText();
             mymap.panDown();
             break;
         case 'panleft':
             setPanZoomHelpText();
             mymap.panLeft();
             break;
         case 'panright':
             setPanZoomHelpText();
             mymap.panRight();
             break;
         case 'panupright':
             setPanZoomHelpText();
             mymap.panUpperRight();
             break;
         case 'pandownright':
             setPanZoomHelpText();
             mymap.panLowerRight();
             break;
         case 'panupleft':
             setPanZoomHelpText();
             mymap.panUpperLeft();
             break;
         case 'pandownleft':
             setPanZoomHelpText();
             mymap.panLowerLeft();
             break;
         case 'reset':
             dojo.byId('help-text').innerHTML = originalHelpText;
             if(originalHelpText == '') {
                dojo.byId('help-text').style.display = 'none';
             }
             mymap.setExtent(mymap.initialExtent);
             changedOriginalText = true;
             break;
         case 'switchBasemap':
             switchBasemap();
             break;
         case 'previousMap':
             --mapIndex;
             if (mapIndex < 0) {
                 mapIndex = webmapgallery.length - 1;
             }
             isBusy = true;
             loadMap(webmapgallery[mapIndex]);
             break;
         case 'nextMap':
             ++mapIndex;
             if (mapIndex > webmapgallery.length - 1) {
                 mapIndex = 0;
             }
             isBusy = true;
             loadMap(webmapgallery[mapIndex]);
             break;
         default:
             break;
     }
 }

 function setPanZoomHelpText() {
     if (changedOriginalText) {
         originalHelpText = dojo.byId('help-text').innerHTML;
         dojo.byId('help-text').style.display = 'inline-block';
         dojo.byId('help-text').innerHTML = 'Press "back" to return to original extent.';
         changedOriginalText = false;
     }
 }

 function switchBasemap() {
     mymap.setBasemap(basemapTypes[basemapIndex % basemapTypes.length]);
     basemapIndex++;
 }