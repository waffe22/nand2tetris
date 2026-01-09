


class Parser():
    def __init__(self,vm_path):
        f=open(vm_path,"r",encoding="utf-8")

        self.index=0
        self.code=[]
        
        for i in f.readlines():
            s=i.split("//")[0].strip()
            l=[]
            for v in s.split(" "):
                if v:
                    l.append(v)
            if l:
                self.code.append(l)
        

        self.command=self.code[self.index]
         

    def hasMoreCommands(self):
        if self.index<len(self.code):
            return True
        else:
            return False
        
    def advance(self):
        
        self.command=self.code[self.index]
        self.index+=1

    def commandType(self):
        first=self.command[0]

        if first in ["add","sub","neg","eq","gt","lt","and","or","not"]:
            return "C_ARITHMETRIC"
        
        d={"push":"C_PUSH","pop":"C_POP",
           "label":"C_LABEL","goto":"C_GOTO","if-goto":"C_IF",
           "function":"C_FUNCTION","return":"C_RETURN","call":"C_CALL"}
        
        if first in d:
            return d[first]
        
        return False

    def arg0(self):
        return self.command[0]
    
    def arg1(self):
        return self.command[1]

    def arg2(self):
        return self.command[2]