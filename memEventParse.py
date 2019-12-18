from pyparsing import nestedExpr as ne
import pyparsing as pp
import sys
import pprint
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

myfile=open(sys.argv[1], 'r')
dbg=int(sys.argv[2])

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

if dbg == 1:
   start.setDebug()
   body.setDebug()
   end.setDebug()

stmt = pp.Forward()
stmt << (comment | start | body | end)
module_body = pp.OneOrMore(stmt)
parseTree = module_body.parseString(lines)
#parseTree.pprint()

stacks={}
stack=[]
for s in parseTree.asList():
    mem = 0
    if "PushRegion" in s:
        stack.append(s[2].strip())
    if "PopRegion" in s:
        stack.pop()
    if "PushRegion" not in s and "PopRegion" not in s:
        mem = int(s[2])
        stackStr = ';'.join(stack)
        if len(s) == 6:
          stackStr += ";" + s[5]
        if stackStr not in stacks:
          stacks[stackStr]=[0]

M=1024*1024
stack=[]
time=[]
mem=[]
tot=0
for s in parseTree.asList():
    if "PushRegion" in s:
        stack.append(s[2].strip())
    if "PopRegion" in s:
        stack.pop()
    if "PushRegion" not in s and "PopRegion" not in s:
        stackStr = ';'.join(stack)
        if len(s) == 6:
          stackStr += ";" + s[5]
        time.append(float(s[0]))
        m = float(s[2])
        tot += m
        mem.append(tot/M)
        for (k,v) in stacks.items():
          last=stacks[k][-1]
          if stackStr == k:
            lpm = last + m/M
            if lpm < 0:
              stacks[k].append(0)
            else:
              stacks[k].append(lpm)
          else:
            stacks[k].append(last)

sortedStacks = sorted(stacks.items(), key=lambda e: max(e[1]),reverse=True)

bigStacks={'time':time}
bigStacks={'other':[]}
i=0
maxEntries=10
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

print(max(bigStacks['other']))

df = pd.DataFrame(bigStacks)
f = plt.figure()
ax = df.plot.area()
ax.legend(bbox_to_anchor=(1,1))
ax.set_ylabel('gpu mem(MB)')
ax.set_title('peak gpu memory usage')
f.subplots_adjust(right=0.8)
plt.savefig(sys.argv[3],bbox_inches='tight',dpi=200)
