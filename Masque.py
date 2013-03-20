from RFExplorer import *

RFE = RFExplorer(4)

def first_chunk():
    """
    Creates the compiled dictionary for the band from 450-512 MHz in 3MHz chunks
    Takes 2 minutes to get all the data
    
    returns compiled dictionary to feed into the CSV creator
    
    """
    start_freq = 450000
    now = time.time()
    end_time = now + 120
    while end_time > now:
        
    
    