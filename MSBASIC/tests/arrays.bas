10 dim a(20), n$(3)
20 for i=0 to 20: a(i)=i*i: next
30 print a(5), a(20)
40 n$(1)="one": n$(3)="three"
50 print n$(1); n$(2); n$(3)
60 dim m(2,3): m(2,3)=7: print m(2,3)+m(0,0)
70 b(10)=1: print b(10)
run
