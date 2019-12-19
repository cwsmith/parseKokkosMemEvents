import pyparsing as pp
import sys
import pandas as pd
import matplotlib.pyplot as plt

if len(sys.argv) is not 4:
    print("Usage:", sys.argv[0],
      "<mem-events file> <max regions> <output plot>")
    sys.exit(1)

filepath = sys.argv[1]
with open(filepath) as f:
      lines = f.read()

integer=pp.Combine(pp.Optional(pp.Word('-')) + pp.Word(pp.nums))
real=pp.Combine(integer + pp.Literal('.') + integer)
hexa=pp.Combine(pp.Word('0x') + pp.Word(pp.alphanums))
string=pp.Word(pp.alphas)
push=pp.Keyword("PushRegion")
pop=pp.Keyword("PopRegion")
ls=pp.Optional(pp.LineEnd()) + pp.LineStart()
underName=pp.Word(pp.alphas+"_", pp.alphanums+"_"+" ")

comment=pp.Suppress(pp.Group(ls + pp.Keyword("#") + pp.SkipTo(pp.LineEnd())))
start=pp.Group(ls + real + push + pp.SkipTo('{',include=True) + pp.LineEnd())
start.setName('start')
body=pp.Group(ls + real + hexa + integer + string + string + pp.Optional(underName))
body.setName('body')
end=pp.Group(ls + real + pp.Keyword('}') + pop + pp.LineEnd())
end.setName('end')

if False: #change to True to debug parsing
   start.setDebug()
   body.setDebug()
   end.setDebug()

stmt = pp.Forward()
stmt << (comment | start | body | end)
module_body = pp.OneOrMore(stmt)
parseTree = module_body.parseString(lines)

def getStackString(stack,s,maxDepth):
  stackStr=''
  if len(s) == 6: # capture the name of the view/allocation
    stack.append(s[5])
  # Omega_h 'Write allocation' frames need to be counted
  # within their parent frame since their deallocation
  # is in the parent frame
  stackStr = ';'.join([i if i != "Write allocation" else '' for i in stack[0:maxDepth]])
  if len(s) == 6:
    stack.pop()
  if len(stackStr) == 0:
    stackStr = "root"
  return stackStr

stacks={}
stack=[]
maxDepth=1
for s in parseTree.asList():
    mem = 0
    if "PushRegion" in s:
        stack.append(s[2].strip())
    if "PopRegion" in s:
        stack.pop()
    if "PushRegion" not in s and "PopRegion" not in s and "Cuda" in s:
        mem = int(s[2])
        stackStr = getStackString(stack,s,maxDepth)
        # add the new stack to the dictionary
        if stackStr not in stacks:
          stacks[stackStr]=[0]

M=1024*1024*1024
stack=[]
#length needs to match the length of lists in 'stacks'
time=[0]
mem=[]
tot=0
for s in parseTree.asList():
    if "PushRegion" in s:
        stack.append(s[2].strip())
    if "PopRegion" in s:
        stack.pop()
    if "PushRegion" not in s and "PopRegion" not in s and "Cuda" in s:
        stackStr = getStackString(stack,s,maxDepth)
        time.append(float(s[0]))
        m = float(s[2])
        tot += m
        mem.append(tot/M)
        for (k,v) in stacks.items():
          last=stacks[k][-1]
          if stackStr == k:
            lpm = last + m/M
            if lpm < 0: # area plots don't support negative values
              stacks[k].append(0)
            else:
              stacks[k].append(lpm)
          else:
            stacks[k].append(last)

sortedStacks = sorted(stacks.items(), key=lambda e: max(e[1]),reverse=True)

bigStacks={'time':time}
bigStacks['other']=[]
i=0
maxEntries=int(sys.argv[2])
for (k,v) in sortedStacks:
    if i < maxEntries:
      bigStacks[k]=v
    else:
      o = bigStacks['other']
      if not o:
        bigStacks['other'] = v;
      else:
        bigStacks['other'] = [sum(x) for x in zip(o,v)]
    i+=1

print('---begin: max mem stacks (region, maxGB) ---')
for (k,v) in bigStacks.items():
  if k != 'time':
    print(k,max(v))
print('---end: max mem stacks---')

df = pd.DataFrame(bigStacks)
f = plt.figure()
ax = df.plot.area(x='time')
#move the legend to the right of the plot
legendTitle="top "+str(maxEntries)+" largest memory usage regions"
ax.legend(title=legendTitle,bbox_to_anchor=(1,1))
ax.set_ylabel('gpu mem (GB)')
ax.set_xlabel('time (s)')
ax.set_title('gpu memory usage')
plt.savefig(sys.argv[3],bbox_inches='tight',dpi=200)
