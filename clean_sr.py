import srmanager.sr

srm = srmanager.sr.SR()

top = srm.get_topology()

srm.del_all_flows(top)
