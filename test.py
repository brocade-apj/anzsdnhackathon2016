import srmanager.sr

srm = srmanager.sr.SR()

top = srm.get_topology()

#for n in top:
#    for l in top[n]:
#        print "{} node, {} link, {} src-tp".format(n,l,top[n][l]['source-tp'])

srm.del_all_flows(top)
srm.add_sr_flows(top)
