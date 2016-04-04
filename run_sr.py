import srmanager.sr

# get SR class
srm = srmanager.sr.SR()

# grab the latest topology
top = srm.get_topology()

# delete all flows
srm.del_all_flows(top)

# now add sr flows
srm.add_sr_flows(top)
