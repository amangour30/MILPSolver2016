from pulp import *
from numpy import *
from copy import *
from math import *
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
		
	
# Solves the MILP : min cTx + dTy such that Ax + Gy <= b where G is integral
def DFSSolver(c,d,A,G,b):
	
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
	#problem stack initially contains the root node
	while size(ProbStack) > 0:
		
		currNode = ProbStack.pop()
		currCode = currNode.code
		#newProb contains a shallow copy of the original problem
		NewProb = OriginalProb.copy()
		
		
		#adding a new constaint to the original problem
		if size(currNode.AddlC) != 0: 
			for i in range(size(currNode.AddlC)):
				NewProb+= currNode.AddlC[i] <= currNode.AddlB[i]
		

		NewProb.solve(cbc_solver)
		#currNode status represent whether the node has been visited or not. 
		#0 - Not Visited
		#1 - Visited but not completed
		#2 - Completed
		currNode.status = 2
		count = 0
		optVal = value(NewProb.objective)
		if LpStatus[NewProb.status]!='Infeasible' and LpStatus[NewProb.status]!='Unbounded' and BestSol > optVal:
			#add heuristic for node selection here
			fracvariables = []
			count = count + 1
			k = 1
			for v in NewProb.variables():
				if v.name[0] == 'y' and v.varValue != floor(v.varValue):
					currNode.status = 0
					branchVar = int(v.name[2:])
					branchPoint = floor(v.varValue)
					if len(fracvariables) < k :
						fracvariables.append([branchVar, branchPoint])
					else:
						break
					#why are we not breaking once we have found the branching variable
					
		if currNode.status == 2 and LpStatus[NewProb.status]=='Optimal' and BestSol > optVal:
			currBestSol = NewProb.copy()
			BestSol = optVal
			
		
		if currNode.status == 0:
			bestVar = 0
			bestBranchPoint = 0
			optvalsofar = float("inf")
			for tempnode in fracvariables:
				branchVar = tempnode[0]
				branchPoint = tempnode[1]
				newNode = LPNode(currCode+'0')
				AddlC = copy(currNode.AddlC)
				AddlB = copy(currNode.AddlB)
				newConst = y[branchVar]
				AddlC.append(newConst)
				AddlB.append(branchPoint)
				newNode.add_Constraint(AddlC,AddlB)
				# ProbStack.append(newNode)
				NewProb2 = OriginalProb.copy()
				#adding a new constaint to the original problem
				if size(newNode.AddlC) != 0: 
					for i in range(size(newNode.AddlC)):
						NewProb2 += newNode.AddlC[i] <= newNode.AddlB[i]

				NewProb2.solve(cbc_solver)
				optVal2 = value(NewProb2.objective)
				
				if LpStatus[NewProb2.status]!='Infeasible' and LpStatus[NewProb2.status]!='Unbounded' and optVal2 < optvalsofar:
					bestVar = branchVar
					bestBranchPoint = branchPoint

			branchVar = bestVar
			branchPoint = bestBranchPoint
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
				#once a new problem is created solve it
		
	if currBestSol == None:	
		return Soln('Infeasible or Unbounded',[],[],float("inf"))
		
	else:
		currBestSol.solve(cbc_solver)
		ySol = dict()
		xSol = dict()
		for v in currBestSol.variables():
				if v.name[0] == 'y':
					ySol[v.name[2:]] = v.varValue
				if v.name[0] == 'x':
					xSol[v.name[2:]] = v.varValue
		print value(currBestSol.objective)
		print ySol
		return Soln('Solved', xSol, ySol, value(currBestSol.objective))
		
	
		
def BFSSolver(c,d,A,G,b):
	
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
			
		
		
	if currBestSol == None:	
		return Soln('Infeasible or Unbounded',[],[],float("inf"))
		
	else:
		currBestSol.solve(cbc_solver)
		ySol = dict()
		xSol = dict()
		for v in currBestSol.variables():
				if v.name[0] == 'y':
					ySol[v.name[2:]] = v.varValue
				if v.name[0] == 'x':
					xSol[v.name[2:]] = v.varValue
		
		print value(currBestSol.objective)
		return Soln('Solved', xSol, ySol, value(currBestSol.objective))

		

def BestFirstSolver(c,d,A,G,b):
	
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
	variables = OriginalProb.variables()
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
				if v.name[0] == 'y' and v.varValue != floor(v.varValue):
					currNode.status = 0
					branchVar = int(v.name[2:])
					branchPoint = floor(v.varValue)
					
		if currNode.status == 2 and currNode.isSolved=='Optimal' and BestSol > optVal:
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
			NewProb = OriginalProb.copy()
			
			if size(AddlC) != 0: 
				for i in range(size(AddlC)):
					NewProb+= AddlC[i] <= AddlB[i]
			
			NewProb.solve(cbc_solver)
			variables = NewProb.variables()
			newNode.sol(variables,LpStatus[NewProb.status],value(NewProb.objective))
			ProbHeap.put((value(OriginalProb.objective),newNode))
						
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
			variables = NewProb.variables()
			newNode.sol(variables,LpStatus[NewProb.status],value(NewProb.objective))
			ProbHeap.put((value(OriginalProb.objective),newNode))
			
			
		
		
	if currBestSol == None:	
		return Soln('Infeasible or Unbounded',[],[],float("inf"))
		
	else:
		currBestSol.solve(cbc_solver)
		ySol = dict()
		xSol = dict()
		for v in currBestSol.variables():
				if v.name[0] == 'y':
					ySol[v.name[2:]] = v.varValue
				if v.name[0] == 'x':
					xSol[v.name[2:]] = v.varValue
		
		print value(currBestSol.objective)
		return Soln('Solved', xSol, ySol, value(currBestSol.objective))

