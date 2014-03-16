#!/usr/bin/python
"""
Example script that sweeps from 450MHz to 698MHz and outputs file to CSV

Just a command line UI
"""

from RFExplorer import *

def first_chunk(RFE):
    """Creates the compiled dictionary for the band from 450-512 MHz in 1.5MHz chunks
        
        Args: RFE :mod: `RFExplorer` instance

        Returns: compiled dictionary to feed into the CSV creator
    
    """
    start_freq = 450000
    end_freq = 512000
    chunks = (end_freq - start_freq)/1550
    freq_list = ['450000']
    for i in range(chunks):
        freq_list.append(int(freq_list[i])+1550)
    end_time = time.time() + 900
    #let's stop  this first chunk after 15 minutes
    first_chunk = {}
    while time.time() < end_time:
        for i in range(chunks):
            start = freq_list[i]
            end = str(int(start)+1550)
            print 'sweeping from %s to %s' % (start, end)
            dict = RFE.timed_sweep(start,end,30)
            for i, v in dict.iteritems():
                if i in first_chunk:
                    if v > first_chunk[i]:
                        first_chunk[i] = v
                else:
                    first_chunk[i] = v
    return first_chunk
    
def second_chunk(RFE):
    """see :func: `first_chunk`
    
    """
    start_freq = 512000
    end_freq = 698000
    chunks = (end_freq - start_freq)/3100
    freq_list = ['512000']
    for i in range(chunks):
        freq_list.append(int(freq_list[i])+3100)
    end_time = time.time() + 900
    #kill it after 15 mins of collecting this band's data
    second_chunk = {}
    #for each chunk, sit for 30 secs
    while time.time() < end_time:
        for i in range(chunks):
            start = freq_list[i]
            end = str(int(start)+3100)
            print 'sweeping from %s to %s for 10sec' % (start, end)
            dict = RFE.timed_sweep(start,end, 10)
            for i, v in dict.iteritems():
                if i in second_chunk:
                    if v > second_chunk[i]:
                        second_chunk[i] = v
                else:
                    second_chunk[i] = v
    return second_chunk
    
def RF_data():
    if os.name != 'nt':
        port = getRFExplorerPort()
    else:
        x = list_serial_ports()
        for i in x:
            print "Here's a list of your serial ports."
            print x
            print "Do you know which number the RFE is?"
            print """
                    If you don't know...remember the above list of ports, 
                    then unplug the RFE and run the program again to determine which number went away from the above list.
                    This is the RFE's port! Remember this port number for the next step.
                  """
            num = raw_input("Which serial port number is the RFE? Only enter the number, not the word 'COM'.>>> ")
            port = int(num)
           #args are getting submitted as strings? this should give it an int...
    RFE = RFExplorer(port)
    filename = raw_input("Enter the name of the CSV file that you want generated.>>> ")
    print 'Sweeping from 450-512...'
    print 'Please wait for the program to exit...'
    d1 = first_chunk(RFE)
    print 'Sweeping from 512-698...'
    d2 = second_chunk(RFE)
    final_dict = dict(d1, **d2)
    success = RFE.make_csv(filename, final_dict)
    return True
    
    
if __name__ == '__main__':
    RF_data()