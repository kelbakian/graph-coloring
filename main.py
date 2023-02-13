import sys
import argparse

#vertices are numbered starting from 1, and nvertices/edges is known, so pre-define things for ease
class Graph():
    def __init__(self,nv,ne,algo):
        self.nvertices = nv
        self.nedges = ne
        #self.vertices = {}
        self.edges = dict.fromkeys(range(nv)+1,[])
        self.algo = algo
    
    def add_vertex(self,v):
        pass
    
    # undirected graph
    def add_edge(self,v1,v2):
        self.edges[v1].append(v2)
        self.edges[v2].append(v1)

    

def main(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument("algo",choices=['dfs','fc','mcv'],required=True)
    parser.add_argument("ncolors",required=True)
    parser.add_argument("-restarts","--restarts",action="store_true",required=False)
    args = parser.parse_args()
    
    #parse the DIMACS graph format subset input
    #graph is undirected, so make sure to draw edges both directions! not given on input
    for line in sys.stdin.readline():
        parsed_line = line.strip().split(' ')
        if parsed_line[0] == 'p':
            nvertices = parsed_line[2]
            nedges = parsed_line[3]
            graph = Graph(nvertices,nedges,args.algo)
        elif parsed_line[0] == 'e':
            v1 = parsed_line[1]
            v2 = parsed_line[2]
            graph.add_edge(v1,v2)
        else: #either a comment or blank line, just cotinue
            continue
    

    #output = DIMACS color format: see spec for details


if __name__ == "__main__":
    main()