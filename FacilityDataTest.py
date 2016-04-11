from numpy import *
import FacilityData
import MILPSolver

print "\nSolving using DFS"
MILPSolver.Solver(FacilityData.c,FacilityData.d,FacilityData.A,FacilityData.G,FacilityData.b,'DFS')

print "\nSolving using BFS"
MILPSolver.Solver(FacilityData.c,FacilityData.d,FacilityData.A,FacilityData.G,FacilityData.b,'BFS')

print "\nSolving using Best-First Search"
MILPSolver.Solver(FacilityData.c,FacilityData.d,FacilityData.A,FacilityData.G,FacilityData.b,'BestFirst')
