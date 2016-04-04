import sroof
import networkx as nx


sroof = sroof.SRoOF()

g = sroof.get_topology()


sroof.add_flows(g)
