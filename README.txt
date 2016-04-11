The MILPSolver solves Mixed integer linear programs of the form

MIN cTx + dTy

subject to 
Ax + Gy <= b
where y is integral.

To use it, import MILPSolver and use MILPSolver.Solver(c,d,A,G,b,method) in your code.
Method can be 'BFS', 'DFS' or 'BestFirst'. If no method is assigned, Best First heuristic will be used to solve the MILP.

The method will return an object of class Soln which has the following components - 
status - 'Feasible', 'Infeasible or Unbounded' 
xSol - x Component of the Optimal Solution
ySol - y Component for the Optimal Solution
optVal - Optimal Value if it exists

For concrete examples, see one of the text files.
 