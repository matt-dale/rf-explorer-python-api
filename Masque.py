from RFExplorer import *

RFE = RFExplorer(5)

def first_chunk(RFE):
    """
    Creates the compiled dictionary for the band from 450-512 MHz in 1.5MHz chunks
    Takes 2 minutes to get all the data
    
    returns compiled dictionary to feed into the CSV creator
    
    """
    start_freq = 450000
    end_freq = 512000
    chunks = (end_freq - start_freq)/1550
    freq_list = ['450000']
    for i in range(chunks):
        freq_list.append(int(freq_list[i])+1550)
    end_time = time.time() + 120
    first_chunk = {}
    while time.time() < end_time:
        for i in range(chunks):
            print i
            start = freq_list[i]
            end = str(int(start)+1550)
            dict = RFE.quick_sweep(start,end)
            for i, v in dict.iteritems():
                if i in first_chunk:
                    if v > first_chunk[i]:
                        first_chunk[i] = v
                else:
                    first_chunk[i] = v
    return first_chunk
    
def second_chunk(RFE):
    """
    Creates the compiled dictionary for the band from 512-698 MHz in 3MHz chunks
    Takes 2 minutes to get all the data
    
    returns compiled dictionary to feed into the CSV creator
    
    """
    start_freq = 512000
    end_freq = 698000
    chunks = (end_freq - start_freq)/3100
    freq_list = ['512000']
    for i in range(chunks):
        freq_list.append(int(freq_list[i])+3100)
    end_time = time.time() + 120
    second_chunk = {}
    while time.time() < end_time:
        for i in range(chunks):
            start = freq_list[i]
            end = str(int(start)+3100)
            dict = RFE.quick_sweep(start,end)
            for i, v in dict.iteritems():
                if i in second_chunk:
                    if v > second_chunk[i]:
                        second_chunk[i] = v
                else:
                    second_chunk[i] = v
    return second_chunk
    
def masque_RF_data(RFE, filename):
    d1 = first_chunk(RFE)
    d2 = second_chunk(RFE)
    final_dict = dict(d1, **d2)
    success = RFE.make_csv(filename, final_dict)
    return True
    
            
            
        
        
    
    