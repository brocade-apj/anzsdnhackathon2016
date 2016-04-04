import srmanager.sr

srm = srmanager.sr.SR()

top = srm.get_topology()

print("Graph Topology:")
for n in top:
    print ("node: {}".format(n))
    for l in top[n]:
        print "  {} link, {} src-tp".format(l,top[n][l]['source-tp'])

