


class VMGenerator():
    def __init__(self):
        self.label_count=0

    def generatePush(self,segment,num):
        return f"push {segment} {num}\n"

    def generatePop(self,segment,num):
        return f"pop {segment} {num}\n"

    def generateArithmetric(self,a):
        return a+"\n"
    
    def generateLabel(self):
        s=f"label L{self.label_count}\n"
        self.label_count+=1
        return [s,f"L{self.label_count-1}"]
    
    def generateGoto(self,label):
        return f"goto {label}\n"
    
    def generateIfGoto(self,label):
        return f"if-goto {label}\n"
    
    def genemrateFunction(self,classname,subroutinename,numlocals):
        return f"function {classname}.{subroutinename} {numlocals}\n"
    
    def generateCall(self,classname,subroutinename,numargs):
        return f"call {classname}.{subroutinename} {numargs}\n"
    
    def generateReturn(self):
        return f"return\n"