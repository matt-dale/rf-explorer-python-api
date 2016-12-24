.. RFExplorer Python API documentation intro

THIS PACKAGE IS OUTDATED. 
PLEASE USE THIS:
https://github.com/RFExplorer/RFExplorer-for-Python/wiki

Intro to the RFExplorer Python API
==================================
The purpose of this API is to provide the structure to script the RFExplorer(http://rfexplorer.com/models/) to gather data for a specific set of frequency ranges.  

In practice, the RFExplorer tool itself can obtain data in chunks that will fit on its window. If you would want to output this data to a file for viewing in an RF coordination program such as IAS, the user would have to manually change the device, run the sweep, save the data for that chunk, then move on to the next chunk. After all the chunks were collected, the user would have to concatenate all the output files into a single CSV for import.  

With this API, you can create some preset options for the frequency ranges that you are interested in.  The code manipulates the RFExplorer, gathers the outputted data and collects it into a single CSV file.  

If you are interested in graphical output and other methods of data collection, please visit `RFExplorer's website.` [4]_ 

Requirements
============
* `Python 2.7` [0]_ of course!
* `Pyserial` [1]_ for serial port access with Python
* `Silicon Labs USB Serial Driver` [2]_ driver for the RFExplorer

Installation and use
====================
Once the requirements are installed, you can begin to write your own scripts using the RFExplorer Class. Confirm that the RFExplorer's baudrate is set to 500kbps.

The base RFExplorer() class takes one argument.  This argument is the COM port string for Mac and Linux and Com Port Number for Windows. 

A Mac should automatically find the Silabs driver, but it needs some testing on Linux.

Then you will have access to the various methods to control the RFExplorer.

There are two preset sweeps in the module to get the base information for an entertainment industry sweep.

If you call the module from the commandline, you will get the basic "DTVSweep" which will save the sweep data to the current working directory.
This is a nice example of the scripting possibilities with the RFExplorer.  




.. [0] http://www.python.org/download/releases/2.7/
.. [1] https://pypi.python.org/pypi/pyserial
.. [2] http://micro.arocholl.com/download/RFExplorer_USB_Driver.zip
.. [4] http://www.rfexplorer.com
