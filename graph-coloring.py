from __future__ import annotations
import sys
import argparse
import random as rand
from collections import defaultdict

sys.setrecursionlimit(1500)
"""Program to color a given graph using a given number of colors such
that no two adjacent vertices have the same color, or prove that no
such coloring is possible. Formulated and approached as a CSP."""

#vertices are numbered starting from 1, and nvertices/edges is known, so pre-define things for ease
class Graph():
    def __init__(self,nv,ne):
        self.nvertices = nv
        self.nedges = ne
        self.edges = defaultdict(list)
    
    # undirected graph
    def add_edge(self,v1,v2):
        self.edges[v1].append(v2)
        self.edges[v2].append(v1)
    
    def __repr__(self):
        return f"Graph(vertices={self.nvertices}, edges={self.nedges},adj list={self.edges})"

class CSP():
    def __init__(self,g,algo,ncolors,restart_flag=False):
        self.graph = g
        self.ncolors = ncolors
        self.algo = algo
        self.X = frozenset(range(1,g.nvertices+1))
        self.D = dict.fromkeys(self.X,set(range(1,ncolors+1)))
        
        self.restart_flag = restart_flag
        

    def __repr__(self):
        return f"CSP(colors={self.ncolors}, X={self.X},D={self.D})"
        
    def solver(self):
        """Returns a DIMACS color file or no solution, and the
        number of branching nodes explored over the search"""
        return self.dfs()

        
    """
    Repeatedly choose an unassigned variable, trying all values in its domain,
    trying to extend each one into a solution via a recursive call.
    If successful returns the solution, if fails assignment is restored
    to the previous state and the next value is tried.
    If no value works returns failure.
    """ 
    def dfs(self):
        if self.restart_flag: # geometric restarting strategy (Walsh,IJCAI-99)
            i = 0
            while True:
                cutoff = self.graph.nvertices * (1.3 ** i)
                n, sol = self.backtrack({},0,cutoff)
                if sol == "restart":
                    i = i+1
                    continue
                else:
                    break
        else:
            n,sol = self.backtrack({},0)

        if sol is None:
            return "No solution.",f"{n} branching nodes explored."
        else:
            return *self.format_sol(sol),f"{n} branching nodes explored."

    def format_sol(self,sol):
        """Converts an assignment from a dict to DIMACS color format"""
        parsed_output = []
        parsed_output.append(f"s col {len(set(sol.values()))}")
        for v in range(1,self.graph.nvertices+1):
            parsed_output.append(f"l {v} {sol[v]}")
        return parsed_output

    
    #implements dfs,fc, and mcv
    def backtrack(self,assignment,n,cutoff=None):
        if len(assignment) == self.graph.nvertices:
            return n,assignment
        if cutoff is not None and n > cutoff:
            return n,"restart"
        var = self.select_unassigned_variable(assignment)
        n += 1
        for value in self.D[var]:
            if self.is_consistent(var,value,assignment):
                assignment[var] = value
                if self.algo == "dfs":
                    result = self.backtrack(assignment,n,cutoff)
                    if result[1] is not None:
                        return result
                else:
                    inferences = self.inference(var,value,assignment)
                    if inferences is not None:
                        # add the inferences to the CSP
                        map(lambda v: self.D[v].remove(value),inferences)
                        result = self.backtrack(assignment,n,cutoff)
                        if result[1] is not None:
                            return result
                        # remove the inferences from the CSP
                        for adj_v in inferences:
                            self.D[adj_v].add(value)
                del assignment[var]
        return n, None

    def select_unassigned_variable(self,assignment):
        """unassigned variable selection, with random tie-breaking for the MCV set"""
        unassigned = tuple(self.X - set(assignment))
        if self.algo == "mcv":  # return a random var from the set of most-constrained-variables
            sub_domain = {k:self.D[k] for k in unassigned}
            mcv = min(map(len,sub_domain.values()))
            if mcv == self.ncolors:
                return rand.choice(unassigned)
            choices = [k for k, v in sub_domain.items() if len(v) == mcv]
            return rand.choice(choices)
        else:  # return any random var
            return rand.choice(unassigned)

    def is_consistent(self,var,val,assignment):
        """Check if the value is a legal assignment;
        ie no constraint violations"""
        for v in self.graph.edges[var]:
            if v in assignment and assignment[v] == val:
                return False
        return True

    def inference(self,var,val,assignment):
        """implements forward checking; arc consistency
        for a given variable"""
        inferences = []
        for adj_v in self.graph.edges[var]:
            if adj_v not in assignment:
                if val in self.D[adj_v]:
                    if len(self.D[adj_v]) == 1:
                        return None
                    else:
                        inferences.append(adj_v)
        return inferences

    
    

def main(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument("algo",choices=['dfs','fc','mcv'])
    parser.add_argument("ncolors",type=int)
    parser.add_argument("-restarts","--restarts",action="store_true",required=False)
    args = parser.parse_args()
    
    #parse the DIMACS graph format subset input
    with sys.stdin as infile:
        for line in infile:
            if line[0] == 'c' or line[0] == " ":
                continue
            else:
                parsed_line = line.strip().split(' ')
                if parsed_line[0] == 'p':
                    nvertices = int(parsed_line[2])
                    nedges = int(parsed_line[3])
                    graph = Graph(nvertices,nedges)
                elif parsed_line[0] == 'e':
                    v1 = int(parsed_line[1])
                    v2 = int(parsed_line[2])
                    # self-loops aren't restricted from input, so if read one terminate early
                    if v1==v2: 
                        print("No solution.\n0 branching nodes explored.")
                        return
                    graph.add_edge(v1,v2)
                else:
                    continue
    
    # Formulate the CSP and outputs DIMACS color file or no sol
    #Max # of colors needed = |V| so reset ncolors if it's > that to save time and space
    if args.ncolors > nvertices:
        args.ncolors = nvertices
    problem = CSP(graph,args.algo,args.ncolors,args.restarts)
    print(*problem.solver(),sep="\n")


if __name__ == "__main__":
    main()
