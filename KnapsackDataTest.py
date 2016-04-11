from numpy import *
import KnapsackData
import MILPSolver

print "\nSolving using DFS"
MILPSolver.Solver(KnapsackData.c,KnapsackData.d,KnapsackData.A,KnapsackData.G,KnapsackData.b,'DFS')

print "\nSolving using BFS"
MILPSolver.Solver(KnapsackData.c,KnapsackData.d,KnapsackData.A,KnapsackData.G,KnapsackData.b,'BFS')

print "\nSolving using Best First Approach"
MILPSolver.Solver(KnapsackData.c,KnapsackData.d,KnapsackData.A,KnapsackData.G,KnapsackData.b)
