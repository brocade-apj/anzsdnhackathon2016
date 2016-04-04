# Segment Routing ID class

class SID():
    '''Class for Segment ID handling'''

    def __init__(self, start=0x3E80):
        '''initialise with start of global block'''
        self.srgb_start = start

    def get_sid(self, ofid):
        '''get the sid from the openflow id'''
        id = int(ofid[ofid.index(':')+1:])
        return self.srgb_start + id
