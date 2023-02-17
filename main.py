from __future__ import annotations
import sys
import argparse
from dataclasses import dataclass
import random as rand
from copy import deepcopy

"""Program to color a given graph using a given number of colors such
that no two adjacent vertices have the same color, or prove that no
such coloring is possible. Formulated and approached as a CSP."""

#A graph node struct? lazy easy soln for now
#already not using w/e ill keep it for now
@dataclass
class Node():
    v: int # the vertex's label
    c: str # the vertex's color

#vertices are numbered starting from 1, and nvertices/edges is known, so pre-define things for ease
class Graph():
    def __init__(self,nv,ne):
        self.nvertices = nv
        self.nedges = ne
        #self.vertices = {}
        self.edges = dict.fromkeys(range(nv)+1,[])
    
    def add_vertex(self,v):
        pass
    
    # undirected graph
    def add_edge(self,v1,v2):
        self.edges[v1].append(v2)
        self.edges[v2].append(v1)

class CSP():
    def __init__(self,g,algo,ncolors,restart_flag=False):
        self.graph = g
        self.ncolors = ncolors
        self.algo = algo
        self.X = [range(g.nvertices)+1] 
        self.D = dict.fromkeys(self.X,[range(ncolors)+1]) 
        #self.C = {}
        #[[[v,*g[v]],lambda adj: g.colors[v] != g.colors[adj]] for v in g.edges.keys()]
        self.restart_flag = restart_flag
        #self.inference_list = [] #store domains when fc'ing?
        """
        potential for self.C:
        c_list = []
        for var in self.X:
            c_list.extend(map(lambda x: tuple(var,x),self.graph[v]))
        #possibly use another map s.t. add dict k-v pair for each c_list item
        #but need to produce value from the iterable-specific relation so idk
        #otw:
        for c in c_list:
            self.C[c] = lambda: self.coloring[c[0]] != self.coloring[c[1]]
        
        #leaning towards just using edge-dict b/c can't store binary
        constraints in dict, but w/o a dict searching is a pain,
        and rel is trivial and consistent
        """

    def solver(self):
        """Returns a DIMACS color file or no solution, and the
        number of branching nodes explored over the search"""
        return self.dfs()
        """
        if self.algo == "dfs":
            return self.dfs()
        elif self.algo == "fc":
            return self.fc()
        else:
            return self.mcv()
        """
        
    """~pg205 txtbook
    repeatedly choose an unassigned variable, try all values in its domain,
    trying to extend each one into a solution via a recursive call.
    If successful returns the solution, if fails assignment is restored
    to the previous state and the next value is tried.
    If no value works we return failure.
    """ 
    def dfs(self):
        n = 0 # track the number of branching nodes explored
        if self.restart_flag: # geometric restarting strategy (Walsh,IJCAI-99)
            i = 0
            while True:
                cutoff = self.graph.nvertices * (1.3 ** i)
                sol = self.backtrack({},n,cutoff)
                if sol == "restart":
                    i = i+1
                    n = 0
                    continue
                else:
                    break
        else:
            sol = self.backtrack({},n)

        if sol is None:
            return "No solution.",f"{n} branching nodes explored."
        else:
            return *self.format_sol(sol),f"{n} branching nodes explored."

    def format_sol(self,sol):
        """Converts an assignment from a dict to DIMACS color format"""
        parsed_output = []
        parsed_output.append(f"s col {len(set(sol.values()))}")
        for v in range(self.graph.nvertices)+1:
            parsed_output.append(f"l {v} {sol[v]}")
        return parsed_output

    
    #implements dfs,fc, and mcv
    def backtrack(self,assignment,n,cutoff=None):
        if len(assignment) == self.graph.nvertices:
            return assignment
        if cutoff is not None and n > cutoff:
            return "restart"
        var = self.select_unassigned_variable(assignment)
        n += 1
        for value in self.D[var]:
        #for value in self.order_domain_values(var,assignment):
            if self.is_consistent(var,value,assignment):
                assignment[var] = value
                if self.algo == "dfs":
                    result = self.backtrack(assignment,n,cutoff)
                    if result is not None:
                        return result
                else:
                    inferences = self.inference(var,value,assignment)
                    if inferences is not None:
                        self.D.update(inferences)
                        #self.D = inferences
                        #self.inference_list.append(inferences)
                        result = self.backtrack(assignment,n,cutoff)
                        if result is not None:
                            return result
                        #self.inference_list.pop()
                        for v in self.graph.edges[var]:
                            self.D[v].append(value)
                del assignment[var]
        return None

    #next 2 fns dicussed 6.3.1, pg 205
    def select_unassigned_variable(self,assignment):
        """variable selection with random tie-breaking"""
        unassigned = set(self.graph.edges) - set(assignment)
        if self.algo == "mcv":
            #return random var from the most-constrained-variable set
            sub_domain = {k:self.D[k] for k in unassigned}
            mcv = min(sub_domain)
            choices = [k for k, v in sub_domain.items() if v == mcv]
            return rand.choice(choices)
        else:
            #return any random var
            return rand.choice(unassigned)

    """
    def order_domain_values(self,var,assignment):
        var_d = []
        for d in self.D[var]:
            if d not in assignment.values():
                var_d.append(d)
        return var_d
    """

    def is_consistent(self,var,val,assignment):
        """Check if the value is a legal assignment;
        ie no constraint violations"""
        for v,c in assignment.items():
            if v in self.graph.edges[var] and val == c:
                return False
        return True
    
    def inference(self,var,val,assignment):
        """implements forward checking; arc consistency
        for a given variable"""
        #get connections to the var we just colored, that are unassigned
        unassigned = set(self.graph.edges[var]) - set(assignment)
        #new domain dictionary for the variables we're changing
        inferences = {}
        for x in unassigned:
            inferences[x] = deepcopy(self.D[x])
            if val in inferences[x]:
                inferences[x].remove(val)
                if inferences[x] == []:
                    return None
        return inferences
        """
        self.D[x].remove(val)
        if self.D[x] == []:
            return None
        """    

    def fc(self):
        """Augmented dfs with forward checking to reduce domains"""
        #same algorithm but uses inference
        pass

    def mcv(self):
        """Augmented fc to branch on the smallest domains.
        Does not implement full arc consistency checking"""
        #already implemented in backtrack through select_unassigned_variable()
        pass

    
    

def main(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument("algo",choices=['dfs','fc','mcv'],required=True)
    parser.add_argument("ncolors",required=True)
    parser.add_argument("-restarts","--restarts",action="store_true",required=False)
    args = parser.parse_args()
    
    #parse the DIMACS graph format subset input
    for line in sys.stdin.readline():
        parsed_line = line.strip().split(' ')
        if parsed_line[0] == 'p':
            nvertices = parsed_line[2]
            nedges = parsed_line[3]
            graph = Graph(nvertices,nedges)
        elif parsed_line[0] == 'e':
            v1 = parsed_line[1]
            v2 = parsed_line[2]
            graph.add_edge(v1,v2)
        else: #either a comment or blank line, just continue
            continue
    
    # Formulate the CSP and outputs DIMACS color file or no sol
    problem = CSP(graph,args.algo,args.ncolors,args.restarts)
    print(*problem.solver(),sep="\n")


if __name__ == "__main__":
    main()
