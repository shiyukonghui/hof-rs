import io, json, os
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
p = os.path.join(R,"transcripts","a98131de-9a72-4623-8aae-1722ab2a704a_session.v3.jsonl.jsonl")
with io.open(p,"r",encoding="utf-8",errors="replace") as f:
    for ln,line in enumerate(f,1):
        if ln!=1496: continue
        obj=json.loads(line)
        def sk(o,d=0):
            pad="  "*d
            if isinstance(o,dict):
                for k,v in o.items():
                    if isinstance(v,(dict,list)):
                        print(pad+k+":")
                        sk(v,d+1)
                    else:
                        s=repr(v)
                        print(pad+k+" = "+(s[:120]))
            elif isinstance(o,list):
                print(pad+"[list len=%d]"%len(o))
                if o: sk(o[0],d+1)
        sk(obj)
        break
