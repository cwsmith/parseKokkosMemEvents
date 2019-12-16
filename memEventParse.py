from pyparsing import nestedExpr as ne
import pyparsing as pp
import sys
import pprint

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

i=0
tot=0
memMax=-1
for s in parseTree.asList():
    mem = 0
    if "PushRegion" not in s and "PopRegion" not in s:
       print(i,'memEvent',s)
       mem = int(s[2])
       i=i+1
    tot += mem
    if mem > memMax:
       memMax = mem
M=1024*1024
print("total mem (MB) max (MB)", tot/M, memMax/M)
