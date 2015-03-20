# New RFExplorer Class
from __future__ import division
import serial
import os
import time
from serial.tools import list_ports
import binascii
import datetime
import Queue
import threading


import base64
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import smtplib
from email.mime.text import MIMEText

GO = '#'+chr(0x04)+'C0'
STOP = '#'+chr(0x04)+'CH'
LCD_OFF = '#'+chr(0x04)+'L0'
LCD_ON = '#'+chr(0x04)+'L1'

#SHUTDOWN DOESN'T WORK RELIABLY
SHUTDOWN = '#'+chr(0x04)+'CS'

#from Thomas at http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
#Not sure if this is the best way of doing this.  We want the name to match SiLabs Driver
#to pass to the RFE serial init
def list_serial_ports():
    """This just lists the serial ports on a computer. It doesn't actually verify that a port is the RFExplorer
    :returns:  list of ports
    :raises: None

   """
    # Windows
    if os.name == 'nt':
        # Scan for available ports.
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append('COM'+str(i + 1))
                s.close()
            except serial.SerialException:
                pass
        return available
    else:
        # Mac / Linux
        return [port[0] for port in list_ports.comports()]     

def getRFExplorerPort():
    """
    Issue #1: before initializing the RFExplorer class, we need to determine the actual port or device name.
    the int() method previsouly used only worked for COM port numbers(Windows only).
    This method is used only on Mac/Linux
    """
    for i in list_ports.comports():
        if 'SLAB_USBtoUART' in i[0]:
            port = i[0]
        else:
            devs = list_serial_ports()
            port = devs[-1]
    return port

class RFExplorer(object):
    """Instantiates an RFExplorer instance. Must take an integer of the COM port list, not the index.
        For example if the COM port that the RFE is attached to is displayed by
        Windows as COM4, then provide the number 4 to the RFExplorer instance.

        Args:
            port: Integer of the COM port that the RF Explorer is attached to from the output of :func:`list_serial_ports`
            port: the 'cleaned' com port from 'getRFExplorerPort'
        Returns:
            ser: A serial.Serial object.
            freq_list: None

        Raises:
            SerialException: could not open port [COMport]: [Error 2] The system cannot find the file specified.

    """
    def __init__(self,port):
        try:
            self.port = port           
            ser = serial.Serial(port)
            ser.baudrate = 500000
            ser.timeout = 5
            self.ser = ser
            self.freq_list = None
            self.C2FResponse = None
            self.startFreq = None
            self.endFreq = None
            self.errorLog = None
        except Exception as e:
            raise e

    def disconnect(self):
        """
        just a clean disconnect
        """
        self.stop_please()
        self.ser.close()
        return True

    def initialize_RFE_connection(self):
        """
        reinitializes the RF Explorer sending data. and Builds the FreqList for the first sweep
        Args:
            None
        Returns:
            device_info: a list of the device's info
        Raises:
            ValueError:"RFE returned a value that was not '4L'"

        Once connected, after writing GO, the device returns first a string beginning with:
        #C2-M
            Example: #C2-M:003,005,01.09
        The next line should be a #C2-F which gives all pertinent info for the data that will stream next
            Example:
                #C2-F:0623213,0027678,-010,-100,0112,1,000,0015000,2700000,0100000,00048,-001
                #C2-F:0507000,0017857,-010,-100,0112,1,000,0015000,2700000,0100000,00018,-001

        """
        self.freq_list = None # helps make sure that the next time we sweep, everything gets rebuilt
        self.freq_list = None
        self.C2FResponse = None
        self.startFreq = None
        self.endFreq = None
        self.stop_please()
        s = self.ser.write(GO)
        #if self.ser.readline().startswith('$S'):
        #    self.setupASweep(self.startFreq, self.endFreq)
        while not self.ser.readline().startswith('$S'):
            self.parseALine(self.ser.readline())

        return True


    def parseALine(self, line):
        """
        given the line, determine what to do with it.
        A #C2-M is just an initializer so do nothing
        A #C2-F is what needs to be parsed into a 112 step frequency list
        A $S is valid data
        """
        # first figure out what we are dealing with
        if line.startswith('#C2-M'):
            line = self.ser.readline()
        if line.startswith('#C2-F'):
            freq_list = self.parse_C2F(line)
            return freq_list
        elif line.startswith('$S'):
            data = self.parseValidData(line)
            return data
        elif line.startswith('Restart'):
            self.errorLog.append(line)
            return 'Restart'
        else:
            raise ValueError('Not a valid response')

    def set_sweep_params(self, start_freq, end_freq, amp_top, amp_bottom):
        """
        Args:
            self
            start_freq: 7 digit value in kHz. Can be between 0240000 and 0959888
            end_freq: 7 digit value in kHz. Can be between 0241112 and 0960000
            amp_top: 4 digit value in dBm include the +/- sign. Between -110 and +005  
            amp_bottom: 4 digit value in dBm include the +/- sign. Between -120 and -005 
        Returns:
            boolean: True designates a successful change of parameters
        Raises:
            ValueError: Incorrect Value submitted
            ValueError: Length of Value is not correct
            ValueError: Write to RFE Failed

        """
        if int(start_freq) < 240000 or int(start_freq) > 959888:
            raise ValueError("start_freq not in bounds")
        if int(end_freq) < 241112 or int(end_freq) > 960000:
            raise ValueError("end_freq not in bounds")
        if int(amp_top) < -110 or int(amp_top) > 5:
            raise ValueError("amp_top not in bounds")
        if int(amp_bottom) < -120 or int(amp_bottom) > -5:
            raise ValueError("amp_bottom not in bounds")
        start_freq = str(start_freq)
        end_freq = str(end_freq)
        amp_top = str(amp_top)
        amp_bottom = str(amp_bottom)
        if len(start_freq) < 7:
            sf_0 = 7-len(start_freq) 
            start_freq = ('0'*sf_0) + start_freq
        if len(end_freq) < 7:
            ef_0 = 7-len(end_freq) 
            end_freq = ('0'*sf_0) + end_freq
        if len(amp_top) != 4:
            raise ValueError("length of amp_top is not 4") 
        sweep_params = '#'+chr(0x20)+'C2-F:'+start_freq+','+end_freq+','+amp_top+','+amp_bottom
        try:
            s = self.ser.write(sweep_params)
            # there should be a check here that self.C2F gets set and freqlist gets set
            while not self.ser.readline().startswith('$'):
                self.parseALine(self.ser.readline())
            return True
        except:
            raise ValueError("write to RFE failed")

    def parse_C2F(self, line):
        """
        creates the 112 frequency list
        if you select a 100-112Mhz span in your example the sweep scan step is:
            (112-100)/112 = 12/112 = 0.107Mhz = 107Khz. 
            For that each scan point will be 100.0, 100.107, 100.214, etc.
        Example:
            '#C2-F:0507000,0017857,-010,-100,0112,1,000,0015000,2700000,0100000,00018,-001\r\n'
            #C2-F:<Start_Freq>, 
                <Freq_Step>, 
                <Amp_Top>, 
                <Amp_Bottom>, 
                <Sweep_Steps>, 
                <ExpModuleActive>, 
                <CurrentMode>, 
                <Min_Freq>, 
                <Max_Freq>, 
                <Max_Span>, 
                <RBW>, 
                <AmpOffset>, 
                <CalculatorMode> 
                <EOL>
            '#C2-F:0507000,0017857,-010,-100,0112,1,000,0015000,2700000,0100000,00018,-001\r\n'

            #C2-F:0691200,0050000,-036,-101,0112,0,000,0240000,0960000,0600000,00048,-001,000\r\n'
        """
        request_config = line.split(':')
        # try:
        if request_config[0] == '#C2-F':# we know this is the Current_Config key
            request_config = request_config[1].split(',')
            self.C2FResponse = request_config
            initStart_Freq = int(request_config[0])*1000 #MAKE THIS Hz
            self.startFreq = initStart_Freq
            
            initFreq_Step = int(request_config[1]) # in Hz
            initSweep_Steps = int(request_config[4])
            
            # initSpan = (int((initFreq_Step * initSweep_Steps) + 500)/1000)*1000 # back to Hz rounded to kHz
            initSpan1 = round((initFreq_Step * initSweep_Steps)/1000) # back to Hz rounded to kHz
            initSpan = initSpan1*1000
            initEndFreq = initSpan + initStart_Freq
            self.endFreq = initEndFreq
            initCenterFreq = initStart_Freq + (initSpan/2)

            freq_list = [str(initStart_Freq)]
            for currentStep in range(int(initSweep_Steps)):
                if currentStep == 0:
                    continue
                #add a new list entry which freqFromStart greater than the startFreq
                freqFromStart = round((currentStep*initFreq_Step)/1000)*1000
                freq_list.append(str(initStart_Freq+freqFromStart))
            self.freq_list = freq_list
            return freq_list
        else: # Should NEVER reach this else
            raise NameError("C2F value is not present in the serial port's queue")
        #except:
        #    return False

    def parseValidData(self, line):
        """
        returns a list of values that correspond with self.freq_list

        Line must start with '$S'
        """
        if self.freq_list == None:
            raise ValueError('Restart collection, there is no corresponding freq_list')
        else:
            results = str(line).split('$Sp')[1]
            itemCount = 0
            separated = []
            for i in results:
                itemCount += 1
                separated.append(ord(i))

            if separated[-1] == 10:
                separated.pop()
                itemCount -= 1
                if separated[-1] == 13:
                    itemCount -= 1
                    separated.pop()  

            if itemCount != 112:
                return 'NOT 112'
            final_results = []
            for i in separated:
                i = int(i)/-2.0#convert to dBm
                final_results.append(i)  
        return final_results

    def setupASweep(self, start, end):
        """
        self explanatory
        """
        top = '-036'
        bottom = '-101'
        sweep_settings = self.set_sweep_params(start,end,top,bottom)
        if sweep_settings != True:
            raise ValueError('Error with setting sweep parameters.')
        else:
            return sweep_settings

    def sweep(self):
        """
        Not a very safe function, but should never be invoked without proper setup first
        """
        if self.freq_list == None:
            try:
                # self.parse_C2F(self.C2FResponse)
                self.initialize_RFE_connection()
            except:
                raise ValueError('Not properly setup to sweep. Please initialize_RFE_connection first.')
        line = self.ser.readline()
        if len(line) == 0:
            raise ValueError('Not properly setup to sweep. Please initialize_RFE_connection first.')

        errorCount = 0
        while not self.ser.readline().startswith('$') and errorCount < 6:
            # need to keep attempting a readline rather than erroring out here. 
            # but give a reasonable errorcount to prevent infinite loop
            line = self.parseALine(self.ser.readline())
            errorCount += 1
        if not self.ser.readline().startswith('$'):
            raise ValueError('Invalid data in the serial queue, please try again.')
        line = self.parseALine(self.ser.readline())
        return line

    def quickSweep(self, start, end):
        # 
        # This is a little dumb here.  We setup the sweep, then stop it, then start again?
        # TODO: why did I do it this way? 
        # self.freq_list should get set when set_sweep_params gets called
        # if we really want a clean start to each window, initialize_RFE should
        # wipe out self.freq_list and start/end, as well as C2Fresponse
        self.initialize_RFE_connection()

        self.setupASweep(start,end)
        results = self.sweep()
        stopCount = 0
        while not len(results) != 112 and stopCount < 10:
            stopCount += 1
            results = self.sweep()
        endData = self.compile_dictionary(results)
        return endData

    def timedSweep(self, start, end, stopTime):
        """
        stopTime is in seconds 
        """
        self.initialize_RFE_connection()
        self.setupASweep(start,end) 
        endTime = datetime.datetime.now() + datetime.timedelta(seconds=stopTime)
        collection = []
        while datetime.datetime.now() < endTime:
            results = self.sweep()
            stopCount = 0
            while not len(results) != 112 and stopCount < 10:
                stopCount += 1
                results = self.sweep()
            for indx, val in enumerate(results):
                if indx in collection:
                    if val > collection[indx]:
                        collection.insert(indx,val)
                else:
                    collection.insert(indx,val)
        endData = self.compile_dictionary(collection)
        self.freq_list = None # helps make sure that the next time we sweep, the freq_list gets rebuilt
        return endData

    def compile_dictionary(self, values):
        freq_dict = {}
        for indx, freq in enumerate(self.freq_list):
            freq_dict[freq] = values[indx]
        return freq_dict

    def DTVSweep(self, queue=None):
        """
        This consolidates all the above functions into 
        a quick and easy scan. 
        Just performs self.quickScan in a fast fashion.
        Returns a combined dictionary of two frequency sets.

        Takes about 12 minutes  

        Queue object can be used to put current sweep details in for UI use


        """
        start_freq = 450000
        end_freq = 512000
        chunks = int(round(((end_freq - start_freq)/2800)))
        freq_list = ['450000']
        for i in range(chunks):
            freq_list.append(int(freq_list[i])+2800)

        first_chunk = {}
        for i in range(chunks):
            start = freq_list[i]
            end = str(int(start)+2800)
            currentString = 'sweeping from %s to %s' % (start, end)
            if queue != None:
                queue.put(currentString)
            else:
                print currentString
            self.startFreq = start
            self.endFreq = end
            freqdict = self.quickSweep(start,end)
            for i, v in freqdict.iteritems():
                first_chunk[i] = v

        start_freq2 = 512000
        end_freq2 = 698000
        chunks2 = int(round(((end_freq2 - start_freq2)/5600)))
        freq_list2 = ['512000']
        for i in range(chunks2):
            freq_list2.append(int(freq_list2[i])+5600)

        second_chunk = {}
        for i in range(chunks2):
            start = freq_list2[i]
            end = str(int(start)+5600)
            currentString = 'sweeping from %s to %s' % (start, end)
            if queue != None:
                queue.put(currentString)
            else:
                print currentString
            self.startFreq = start
            self.endFreq = end
            dict2 = self.quickSweep(start,end)
            for i, v in dict2.iteritems():
                second_chunk[i] = v

        return dict(first_chunk, **second_chunk)

    def longSweep(self, queue=None):
        """
        a much longer sweep that records the peak value 
        while sweeping over a window for a given time.

        Can use Queue to put current sweep details in for UI use
        """
        start_freq = 450000
        end_freq = 512000
        chunks = int((end_freq - start_freq)/2800)
        freq_list = ['450000']
        for i in range(chunks):
            freq_list.append(int(freq_list[i])+2800)

        first_chunk = {}
        for i in range(chunks):
            start = freq_list[i]
            end = str(int(start)+2800)
            currentString = 'sweeping from %s to %s' % (start, end)
            if queue != None:
                queue.put(currentString)
            else:
                print currentString
            freqdict = self.timedSweep(start,end,2)
            for i, v in freqdict.iteritems():
                if i in first_chunk:
                    if v > first_chunk[i]:
                        first_chunk[i] = v
                else:
                    first_chunk[i] = v


        start_freq = 512000
        end_freq = 698000
        chunks = int((end_freq - start_freq)/5600)
        freq_list2 = ['512000']
        for i in range(chunks):
            freq_list2.append(int(freq_list2[i])+5600)

        second_chunk = {}
        for i in range(chunks):
            start = freq_list2[i]
            end = str(int(start)+5600)
            currentString = 'sweeping from %s to %s' % (start, end)
            if queue != None:
                queue.put(currentString)
            else:
                print currentString
            dict2 = self.timedSweep(start,end,2)
            for i, v in dict2.iteritems():
                if i in second_chunk:
                    if v > second_chunk[i]:
                        second_chunk[i] = v
                else:
                    second_chunk[i] = v
        return dict(first_chunk, **second_chunk)


    def stop_please(self):
        self.ser.write(STOP)
        time.sleep(0.25)
        self.ser.flushOutput()
        self.ser.flushInput()
        self.ser.readline()

    def make_csv(self, filename, freq_dict):
        """
        creates the final CSV file by converting all Hz values to MHz
        sorts the results dictionary and writes the file.
        Args: 
            filename: the name of the file that will be saved to the working directory
            freq_dict: a dictionary of freq in kHz, dBm value pairs
        Returns: 
            file: CSV file with filename of filename arg formatted correctly
        Raises:
            
        """
        if filename.endswith('.csv'):
            file = filename
        else:
            file = str(filename)+'.csv'
        fout = open(file, 'w')
        freq_dict = sorted(freq_dict.items())
        """for i, v in freq_dict:
            x = ''
            for j in str(i)[0:3]:
                x += j
            x+='.'
            for j in str(i)[4:7]:
                x += j
            fout.write(str(x)+','+str(v)+'\n')"""
        for i, v in freq_dict:
            theFreq = i[0:3]+'.'+i[3:6]
            fout.write(theFreq+','+str(v)+'\n')
        fout.close()
        return True


def makeFilename(show,city,venue):
    """
    just a parser for creating the CSV filename
    """
    name = 'RFExplorerSweep_'+city+'_'+venue+'.csv'
    return name

def RFExplorerSweepThenEmail(show, city, venue, RFE, queue):
    """

    """
    final_dict = RFE.DTVSweep(queue)
    #final_dict = RFE.longSweep(queue)
    filename = makeFilename(show,city,venue)
    success = RFE.make_csv(filename, final_dict)
    # send_email(show,city,venue,filename)
    return True

def RFESweep(show,venue,city,queue,RFE):
    """
    uses the RFE class to start a sweep and email its results
    """
    try:
        show = show.strip(' ').replace('.','').replace('/', '_').replace(''''\'''', '_')
    except:
        pass
    try:
        city = city.strip(' ').replace('.','').replace('/', '_').replace(''''\'''', '_')
    except:
        pass
    try:
        venue = venue.strip(' ').replace('.','').replace('/', '_').replace(''''\'''', '_')
    except:
        pass      
    try:
        t = threading.Thread(target=RFExplorerSweepThenEmail,
                            #args=[ser,email,filename],
                            args=[show,city,venue,RFE,queue],
                            kwargs = {})
        t.setDaemon(True)
        t.start()
        return t
    except Exception as e:
        return 'Oh No! sweep failed---- %s' % e  
