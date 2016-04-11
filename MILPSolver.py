from pulp import *
from numpy import *
from copy import *
from math import *
import time

try:
    from Queue import * # ver. < 3.0
except ImportError:
    from queue import *
	
cbc_solver = solvers.PULP_CBC_CMD(path=None,msg=0)

class Soln:
	def __init__(self,status,xSol,ySol,optVal):
		self.status = status
		self.xSol = xSol
		self.ySol = ySol
		self.optVal = optVal

class LPNode:
	def __init__(self,code):
		self.code = code
		self.status = 0
		self.AddlC = []
		self.AddlB = []
		
	def add_Constraint(self, AddlConstraints,AddlB):
		self.AddlC = AddlConstraints
		self.AddlB = AddlB
		
	def sol(self, variables, isSolved, optVal):
		self.variables = variables
		self.isSolved = isSolved
		self.optVal = optVal
		
	def Bounds(self, UB):
		self.UB = UB
		
	def updateStatus(self,status):
		self.status = status
		
	
# Solves the MILP : min cTx + dTy such that Ax + Gy <= b where y is integral
def Solver(c,d,A,G,b,method = 'BestFirst'):
	if method == 'DFS':
		return DFSSolver(c,d,A,G,b)
	elif method == 'BestFirst':
		return BestFirstSolver(c,d,A,G,b)
	elif method == 'BFS':
		return BFSSolver(c,d,A,G,b)
	else:
		print 'No such method exists'
		return None

def DFSSolver(c,d,A,G,b):
	t0 = time.clock()
	xSize = size(c)
	ySize = size(d)
	consSize = len(A)
		
	OriginalProb = LpProblem("OrigProb",LpMinimize)
	x = LpVariable.dicts("x", range(xSize),  cat="Continuous")
	y = LpVariable.dicts("y", range(ySize),  cat="Continuous")
	
	# Formulating the objective function
	Obj1 = LpAffineExpression([x[i],c[i]] for i in range(xSize))
	Obj2 = LpAffineExpression([y[i],d[i]] for i in range(ySize))
	Objective = Obj1 + Obj2
	OriginalProb+= Objective
	
	#Adding the original constraints
	for i in range(consSize):
		Const = LpAffineExpression([x[j],A[i][j]] for j in range(xSize))
		Const = Const + LpAffineExpression([y[j],G[i][j]] for j in range(ySize))
		OriginalProb+= Const <= b[i]
	
	
	liveNodes = dict()
	ProbStack = []
	RootNode = LPNode('2')
	liveNodes['2'] = RootNode
	ProbStack.append(RootNode)
	BestSol = float("inf")
	currBestSol = None
	while size(ProbStack) > 0:
		
		
		currNode = ProbStack.pop()
		currCode = currNode.code
		NewProb = OriginalProb.copy()
		
		if size(currNode.AddlC) != 0: 
			for i in range(size(currNode.AddlC)):
				NewProb+= currNode.AddlC[i] <= currNode.AddlB[i]
		
		NewProb.solve(cbc_solver)
		currNode.status = 2
		
		optVal = value(NewProb.objective)
		if LpStatus[NewProb.status]!='Infeasible' and LpStatus[NewProb.status]!='Unbounded' and BestSol > optVal:
			for v in NewProb.variables():
				if v.name[0] == 'y' and v.varValue != floor(v.varValue):
					currNode.status = 0
					branchVar = int(v.name[2:])
					branchPoint = floor(v.varValue)
					break
					
		if currNode.status == 2 and LpStatus[NewProb.status]=='Optimal' and BestSol > optVal:
			currBestSol = NewProb.copy()
			BestSol = optVal
			
			
		if currNode.status == 0:
			newNode = LPNode(currCode+'0')
			AddlC = copy(currNode.AddlC)
			AddlB = copy(currNode.AddlB)
			newConst = y[branchVar]
			AddlC.append(newConst)
			AddlB.append(branchPoint)
			newNode.add_Constraint(AddlC,AddlB)
			ProbStack.append(newNode)
			
			newNode = LPNode(currCode+'1')
			AddlC = copy(currNode.AddlC)
			AddlB = copy(currNode.AddlB)
			newConst = -y[branchVar]
			AddlC.append(newConst)
			AddlB.append(-branchPoint - 1)
			newNode.add_Constraint(AddlC,AddlB)
			ProbStack.append(newNode)
			
		
		
	print "Total Time Taken - ", round(time.clock()-t0,2)," seconds"
	if currBestSol == None:	
		print "The Problem is either infeasible or unbounded"
		return Soln('Infeasible or Unbounded',[],[],float("inf"))
		
	else:
		currBestSol.solve(cbc_solver)
		ySol = dict()
		xSol = dict()
		for v in currBestSol.variables():
				if v.name[0] == 'y':
					ySol[int(v.name[2:])] = v.varValue
				if v.name[0] == 'x':
					xSol[int(v.name[2:])] = v.varValue
		print "The optimal value is", value(currBestSol.objective)
		return Soln('Solved', xSol, ySol, value(currBestSol.objective))
		
	
		
def BFSSolver(c,d,A,G,b):
	
	t0=time.clock()
	xSize = size(c)
	ySize = size(d)
	consSize = len(A)
		
	OriginalProb = LpProblem("OrigProb",LpMinimize)
	x = LpVariable.dicts("x", range(xSize),  cat="Continuous")
	y = LpVariable.dicts("y", range(ySize),  cat="Continuous")
	
	# Formulating the objective function
	Obj1 = LpAffineExpression([x[i],c[i]] for i in range(xSize))
	Obj2 = LpAffineExpression([y[i],d[i]] for i in range(ySize))
	Objective = Obj1 + Obj2
	OriginalProb+= Objective
	
	#Adding the original constraints
	for i in range(consSize):
		Const = LpAffineExpression([x[j],A[i][j]] for j in range(xSize))
		Const = Const + LpAffineExpression([y[j],G[i][j]] for j in range(ySize))
		OriginalProb+= Const <= b[i]
	
	
	liveNodes = dict()
	ProbQueue = []
	RootNode = LPNode('2')
	liveNodes['2'] = RootNode
	ProbQueue.append(RootNode)
	BestSol = float("inf")
	currBestSol = None
	while size(ProbQueue) > 0:
		
		currNode = ProbQueue.pop()
		currCode = currNode.code
		NewProb = OriginalProb.copy()
		
		if size(currNode.AddlC) != 0: 
			for i in range(size(currNode.AddlC)):
				NewProb+= currNode.AddlC[i] <= currNode.AddlB[i]
		
		NewProb.solve(cbc_solver)
		currNode.status = 2
		optVal = value(NewProb.objective)
		
		if LpStatus[NewProb.status]!='Infeasible' and LpStatus[NewProb.status]!='Unbounded' and BestSol > optVal:
			for v in NewProb.variables():
				if v.name[0] == 'y' and v.varValue != floor(v.varValue):
					currNode.status = 0
					branchVar = int(v.name[2:])
					branchPoint = floor(v.varValue)
					break
					
		if currNode.status == 2 and LpStatus[NewProb.status]=='Optimal' and BestSol > optVal:
			currBestSol = NewProb.copy()
			BestSol = optVal
			
		if currNode.status == 0:
			newNode = LPNode(currCode+'0')
			AddlC = copy(currNode.AddlC)
			AddlB = copy(currNode.AddlB)
			newConst = y[branchVar]
			AddlC.append(newConst)
			AddlB.append(branchPoint)
			newNode.add_Constraint(AddlC,AddlB)
			ProbQueue.insert(0,newNode)
						
			newNode = LPNode(currCode+'1')
			AddlC = copy(currNode.AddlC)
			AddlB = copy(currNode.AddlB)
			newConst = -y[branchVar]
			AddlC.append(newConst)
			AddlB.append(-branchPoint - 1)
			newNode.add_Constraint(AddlC,AddlB)
			ProbQueue.insert(0,newNode)
			
		
	print "Total Time Taken - ", round(time.clock()-t0,2)," seconds"	
	if currBestSol == None:
		print "The Problem is either infeasible or unbounded"	
		return Soln('Infeasible or Unbounded',[],[],float("inf"))
		
	else:
		currBestSol.solve(cbc_solver)
		ySol = dict()
		xSol = dict()
		for v in currBestSol.variables():
				if v.name[0] == 'y':
					ySol[int(v.name[2:])] = v.varValue
				if v.name[0] == 'x':
					xSol[int(v.name[2:])] = v.varValue
		
		print "The optimal value is", value(currBestSol.objective)
		return Soln('Solved', xSol, ySol, value(currBestSol.objective))

		

def BestFirstSolver(c,d,A,G,b):
	
	t0=time.clock()
	xSize = size(c)
	ySize = size(d)
	consSize = len(A)
		
	OriginalProb = LpProblem("OrigProb",LpMinimize)
	x = LpVariable.dicts("x", range(xSize),  cat="Continuous")
	y = LpVariable.dicts("y", range(ySize),  cat="Continuous")
	
	# Formulating the objective function
	Obj1 = LpAffineExpression([x[i],c[i]] for i in range(xSize))
	Obj2 = LpAffineExpression([y[i],d[i]] for i in range(ySize))
	Objective = Obj1 + Obj2
	OriginalProb+= Objective
	
	#Adding the original constraints
	for i in range(consSize):
		Const = LpAffineExpression([x[j],A[i][j]] for j in range(xSize))
		Const = Const + LpAffineExpression([y[j],G[i][j]] for j in range(ySize))
		OriginalProb+= Const <= b[i]
	
	
	liveNodes = dict()
	ProbHeap = PriorityQueue()
	RootNode = LPNode('2')
	liveNodes['2'] = RootNode
	OriginalProb.solve(cbc_solver)
	
	variables = dict()
	for v in OriginalProb.variables():
		variables[v.name] = v.varValue
	RootNode.sol(variables,LpStatus[OriginalProb.status],value(OriginalProb.objective))
	ProbHeap.put((value(OriginalProb.objective),RootNode))
	BestSol = float("inf")
	currBestSol = None
	while ProbHeap.empty() == False:
		
		currNode = ProbHeap.get()[1]
		currCode = currNode.code
		currNode.status = 2

		optVal = currNode.optVal
		
		if currNode.isSolved!='Infeasible' and currNode.isSolved!='Unbounded' and BestSol > optVal:
			for v in currNode.variables:
				if v[0] == 'y' and currNode.variables[v] != floor(currNode.variables[v]):
					currNode.status = 0
					branchVar = int(v[2:])
					branchPoint = floor(currNode.variables[v])
					break
					
		if currNode.status == 2 and currNode.isSolved=='Optimal' and BestSol > optVal:
			currBestSol = currNode.variables
			BestSol = optVal
						
		if currNode.status == 0:
			newNode = LPNode(currCode+'0')
			AddlC = copy(currNode.AddlC)
			AddlB = copy(currNode.AddlB)
			newConst = y[branchVar]
			AddlC.append(newConst)
			AddlB.append(branchPoint)
			newNode.add_Constraint(AddlC,AddlB)
			NewProb = OriginalProb.copy()
			
			if size(AddlC) != 0: 
				for i in range(size(AddlC)):
					NewProb+= AddlC[i] <= AddlB[i]
			
			NewProb.solve(cbc_solver)
			
			variables = dict()
			for v in NewProb.variables():
					variables[v.name] = v.varValue
			newNode.sol(variables,LpStatus[NewProb.status],value(NewProb.objective))
			ProbHeap.put((value(NewProb.objective),newNode))
			
						
			newNode = LPNode(currCode+'1')
			AddlC = copy(currNode.AddlC)
			AddlB = copy(currNode.AddlB)
			newConst = -y[branchVar]
			AddlC.append(newConst)
			AddlB.append(-branchPoint - 1)
			newNode.add_Constraint(AddlC,AddlB)
			NewProb = OriginalProb.copy()
			
			if size(AddlC) != 0: 
				for i in range(size(AddlC)):
					NewProb+= AddlC[i] <= AddlB[i]
			
			NewProb.solve(cbc_solver)
			variables = dict()
			for v in NewProb.variables():
					variables[v.name] = v.varValue
			newNode.sol(variables,LpStatus[NewProb.status],value(NewProb.objective))
			ProbHeap.put((value(NewProb.objective),newNode))
			
			
		
	print "Total Time Taken - ", round(time.clock()-t0,2)," seconds"	
	if currBestSol == None:
		print "The Problem is either infeasible or unbounded"	
		return Soln('Infeasible or Unbounded',[],[],float("inf"))
		
	else:
		ySol = dict()
		xSol = dict()
		for v in currBestSol:
				if v == 'y':
					ySol[int(v[2:])] = currBestSol[v]
				if v == 'x':
					xSol[int(v[2:])] = currBestSol[v]
					
		print "The optimal value is", BestSol
		return Soln('Solved', xSol, ySol, BestSol)

