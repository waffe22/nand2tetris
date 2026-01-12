


func_call_counts={}

class CodeWriter():
    def __init__(self,asm_path):
        self.f=open(asm_path,"w",encoding="utf-8")
        self.functionName="null"

    def setFileName(self,vm_path):

        name=vm_path.split(".")[0].split("\\")[-1]
        self.filename=name

    def writeArithmetric(self,command):
        if command in ["not","neg"]:
            numOperands=1
        else:
            numOperands=2
        
        d={"add":"+","sub":"-","neg":"-","and":"&","or":"|","not":"!"}
        
        if command in ["eq","gt","lt"]:
            x=str(func_call_counts.setdefault(command,0))
            func_call_counts[command]+=1
            c=command.upper()
            return f"@RET_ADDRESS_{c+x}\nD=A\n@R15\nM=D\n@{c}\n0;JMP\n(RET_ADDRESS_{c+x})\n"

        if numOperands==1:
            return f"@SP\nA=M-1\nM={d[command]}M\n"
        if numOperands==2:
            return f"@SP\nAM=M-1\nD=M\nA=A-1\nM=M{d[command]}D\n"


    def writePushPop(self,command,segment,index):
        if segment=="constant":
            if index in ["0","1"]:
                return f"@SP\nM=M+1\nA=M-1\nM={index}\n"
            return f"@{index}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        if segment=="static":
            if command=="push":
                return f"@{self.filename}_{str(index)}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
            if command=="pop":
                return f"@SP\nAM=M-1\nD=M\n@{self.filename}_{str(index)}\nM=D\n"
        d={"argument":"ARG","local":"LCL","pointer":"3","this":"THIS","that":"THAT","temp":"5"}
        if segment in d:
            if command=="push":
                if segment in ["pointer","temp"]:
                    return f"@{int(d[segment])+int(index)}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
                if int(index)==0:
                    return f"@{d[segment]}\nA=M\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
                else:
                    return f"@{d[segment]}\nD=M\n@{index}\nA=A+D\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
            if command=="pop":
                if segment in ["pointer","temp"]:
                    if segment=="temp" and index==0:
                        return f"@SP\nM=M-1\n"
                    return f"@SP\nAM=M-1\nD=M\n@{int(index)+int(d[segment])}\nM=D\n"
                
                if int(index)==0:
                    return f"@SP\nAM=M-1\nD=M\n@{d[segment]}\nA=M\nM=D\n"
                elif int(index)<7:
                    inc="A=A+1\n"*int(index)
                    return f"@SP\nAM=M-1\nD=M\n@{d[segment]}\nA=M\n{inc}\nM=D\n"
                else:
                    return f"@{d[segment]}\nD=M\n@{index}\nD=A+D\n@R15\nM=D\n@SP\nAM=M-1\nD=M\n@R15\nA=M\nM=D\n"


    def writeLabel(self,label):
        return f"({self.functionName}${label})\n"

    def writeGoto(self,label):
        return f"@{self.functionName}${label}\n0;JMP\n"

    def writeIf(self,label):
        return f"@SP\nAM=M-1\nD=M\n@{self.functionName}${label}\nD;JNE\n"

    def writeFunction(self,functionName,numLocals):
        print(functionName,numLocals)
        self.functionName=functionName
        x=str(func_call_counts.setdefault("function",0))
        func_call_counts["function"]+=1
        return f"({functionName})\n@RET_ADDRESS_FUNCTION_{x}\nD=A\n@R14\nM=D\n@{numLocals}\nD=A\n@R15\nM=D\n@FUNCTION\n0;JMP\n(RET_ADDRESS_FUNCTION_{x})\n"

    def writeReturn(self):
        return f"@RETURN\n0;JMP\n"
        
    def writeCall(self,functionName,numArgs):
        x=str(func_call_counts.setdefault("call",0))
        func_call_counts["call"]+=1
        return f"@{functionName}\nD=A\n@R15\nM=D\n@{numArgs}\nD=A\n@R14\nM=D\n"+\
            f"@RET_ADDRESS_CALL_{x}\nD=A\n@CALL\n0;JMP\n(RET_ADDRESS_CALL_{x})\n"

    def writeInIt(self):
        _return=f"(RETURN)\n@LCL\nD=M\n@R13\nM=D\n@5\nA=D-A\nD=M\n@R14\nM=D\n@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D\n@ARG\nD=M+1\n@SP\nM=D\n@R13\nAM=M-1\nD=M\n@THAT\nM=D\n@R13\nAM=M-1\nD=M\n@THIS\nM=D\n@R13\nAM=M-1\nD=M\n@ARG\nM=D\n@R13\nAM=M-1\nD=M\n@LCL\nM=D\n@R14\nA=M\n0;JMP\n"
        
        call=f"(CALL)\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"+\
        f"@SP\nD=M\n@R14\nD=D-M\n@5\nD=D-A\n@ARG\nM=D\n@SP\nD=M\n@LCL\nM=D\n@R15\nA=M\n0;JMP\n"

        function=f"(FUNCTION)\n"+ \
            f"(PUSH_ZERO)\n@R15\nD=M\n@PUSH_ZERO_END\nD;JLE\n@0\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@R15\nM=M-1\n"+\
            f"@PUSH_ZERO\n0;JMP\n(PUSH_ZERO_END)\n@R14\nA=M\n0;JMP\n"
        
        eq=f"(EQ)\n@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@EQ_TRUE\nD;JEQ\n@0\nD=A\n@SP\nA=M-1\nM=D\n@R15\nA=M\n0;JMP\n(EQ_TRUE)\n@0\nD=A\n@SP\nA=M-1\nM=D-1\n@R15\nA=M\n0;JMP\n"

        gt=f"(GT)\n@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@GT_TRUE\nD;JGT\n@0\nD=A\n@SP\nA=M-1\nM=D\n@R15\nA=M\n0;JMP\n(GT_TRUE)\n@0\nD=A\n@SP\nA=M-1\nM=D-1\n@R15\nA=M\n0;JMP\n"

        lt=f"(LT)\n@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n@LT_TRUE\nD;JLT\n@0\nD=A\n@SP\nA=M-1\nM=D\n@R15\nA=M\n0;JMP\n(LT_TRUE)\n@0\nD=A\n@SP\nA=M-1\nM=D-1\n@R15\nA=M\n0;JMP\n"

        boot=f"@256\nD=A\n@SP\nM=D\n"+self.writeCall("Sys.init",0)

        return boot+lt+gt+eq+function+call+_return
    
    def write(self,text):
        self.f.write(text)

    def close(self):
        self.f.close()