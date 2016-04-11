from numpy import *
import tsp
import MILPSolver

print "\nSolving using DFS"
MILPSolver.Solver(tsp.c,tsp.d,tsp.A,tsp.G,tsp.b,'DFS')

print "\nSolving using BFS"
MILPSolver.Solver(tsp.c,tsp.d,tsp.A,tsp.G,tsp.b,'BFS')

print "\nSolving using Best-First Search"
MILPSolver.Solver(tsp.c,tsp.d,tsp.A,tsp.G,tsp.b,'BestFirst')
