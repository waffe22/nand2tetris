
from pprint import pprint,pformat


class GenerateEngine():
    def __init__(self,symbol_table,vm_generator):
        self.table=symbol_table
        self.vm_generator=vm_generator
        self.classname=""

        self.subroutinefunc=""
        self.subroutinetype=""
        self.subroutinename=""

    def engine(self,structure):
        vmcode=""
        if type(structure)==dict:
            for i,k in structure.items():
                if i=="class":
                    self.processclass(k)
                if i=="classVarDec":
                    self.processclassVarDec(k)
                    continue
                if i=="parameterList":
                    self.processparameterList(k)
                    continue
                if i=="varDec":
                    self.processvarDec(k)
                    continue
                if i=="letStatement":
                    vmcode+=self.processletStatement(k)
                    continue
                if i=="doStatement":
                    vmcode+=self.processdoStatement(k)
                    continue
                if i=="returnStatement":
                    vmcode+=self.processreturnStatement(k)
                    continue
                if i=="expression":
                    vmcode+=self.processexpression(k)
                    continue
                if i=="subroutineCall":
                    vmcode+=self.processsubroutineCall(k)
                    continue
                if i=="expressionList":
                    vmcode+=self.processexpressionList(k)
                    continue
                
                if i=="ifStatement":
                    vmcode+=self.processifStatement(k)
                    continue
                if i=="whileStatement":
                    vmcode+=self.processwhileStatement(k)
                    continue
                if i=="subroutineDec":
                    self.processsubroutineDec(k)
                    

                if type(k)==list:
                    if i=="subroutineBody":
                        f=False
                        for j in k:
                            if not any(["varDec" in j,"symbol" in j,f]):
                                vmcode+=self.generate_vm_function_dec()
                                f=True
                            vmcode+=self.engine(j)
                    else:
                        for j in k:
                            vmcode+=self.engine(j)
                else:
                    pass
        elif type(structure)==list:
            
            for i in structure:

                vmcode+=self.engine(i)
            
        return vmcode


    
    def processclass(self,structure):
        self.table.flush("field")
        self.classname=structure[1]["identifier"]

    def processsubroutineDec(self, k):
        self.table.flush("arg")
        self.table.flush("var")
        self.subroutinefunc=k[0]["keyword"]
        self.subroutinetype=k[1].get("identifier") or k[1].get("keyword")
        self.subroutinename=k[2]["identifier"]

    def generate_vm_function_dec(self):
        vmcode=""
        numlocals=len(self.table.var_table)
        
        if self.subroutinefunc=="constructor":
            numfields=len(self.table.field_table)
            vmcode+=self.vm_generator.genemrateFunction(self.classname,self.subroutinename,numlocals)

            vmcode+=self.vm_generator.generatePush("constant",numfields)
            vmcode+=self.vm_generator.generateCall("Memory","alloc","1")
            vmcode+=self.vm_generator.generatePop("pointer","0")
        if self.subroutinefunc=="method":
            vmcode+=self.vm_generator.genemrateFunction(self.classname,self.subroutinename,numlocals+1)
            vmcode+=self.vm_generator.generatePush("argument","0")
            vmcode+=self.vm_generator.generatePop("pointer","0")
        if self.subroutinefunc=="function":
            vmcode+=self.vm_generator.genemrateFunction(self.classname,self.subroutinename,numlocals)

        return vmcode

    def processclassVarDec(self,structure):
        scope=structure[0]["keyword"]
        type=structure[1].get("identifier") or structure[1].get("keyword")

        for i in range(2,len(structure),2):
            name=structure[i]["identifier"]
            self.table.add(scope,type,name)

    def processparameterList(self,structure):
        scope="arg"
        for i in range(0,len(structure),3):
            type=structure[i].get("identifier") or structure[i].get("keyword")
            name=structure[i+1]["identifier"]
            self.table.add(scope,type,name)

    def processvarDec(self,structure):
        scope=structure[0]["keyword"]
        type=structure[1].get("identifier") or structure[1].get("keyword")

        for i in range(2,len(structure),2):
            name=structure[i]["identifier"]
            self.table.add(scope,type,name)

    def processletStatement(self,structure):
        vmcode=""
        bracket=structure[2].get("symbol")

        if bracket=="[":
            name=name=structure[1].get("identifier")
            segment,num,_=self.table.find(name)
            vmcode+=self.vm_generator.generatePush(segment,num)
            vmcode+=self.processexpression(structure[3]["expression"])
            vmcode+=self.vm_generator.generateArithmetric("add")
            vmcode+=self.vm_generator.generatePop("pointer","1")
            vmcode+=self.processexpression(structure[6]["expression"])
            vmcode+=self.vm_generator.generatePop("that","0")
        else:
            vmcode+=self.processexpression(structure[3]["expression"])
            name=structure[1].get("identifier")
            segment,num,_=self.table.find(name)

            vmcode+=self.vm_generator.generatePop(segment,num)

        return vmcode

    def processifStatement(self,structure):
        vmcode=""
        c1,l1=self.vm_generator.generateLabel()

        vmcode+=self.processexpression(structure[2]["expression"])
        vmcode+=self.vm_generator.generateArithmetric("not")
        vmcode+=self.vm_generator.generateIfGoto(l1)
        
        vmcode+=self.engine(structure[5])
        
        if len(structure)>10:
            c2,l2=self.vm_generator.generateLabel()
            vmcode+=self.vm_generator.generateGoto(l2)
            vmcode+=c1
            vmcode+=self.engine(structure[9]["statements"])
            vmcode+=c2
        else:
            vmcode+=c1
        return vmcode

    def processwhileStatement(self,structure):
        vmcode=""
        c1,l1=self.vm_generator.generateLabel()
        c2,l2=self.vm_generator.generateLabel()
        vmcode+=c1
        vmcode+=self.processexpression(structure[2]["expression"])
        vmcode+=self.vm_generator.generateArithmetric("not")
        vmcode+=self.vm_generator.generateIfGoto(l2)
        
        vmcode+=self.engine(structure[5]["statements"])
        vmcode+=self.vm_generator.generateGoto(l1)
        vmcode+=c2
        return vmcode

    def processdoStatement(self,structure):
        vmcode=""
        vmcode+=self.processsubroutineCall(structure[1]["subroutineCall"])
        vmcode+=self.vm_generator.generatePop("temp", "0")
        return vmcode

    def processreturnStatement(self,structure):
        vmcode=""

        if len(structure)==3:
            vmcode+=self.processexpression(structure[1]["expression"])
        else:
            vmcode+=self.vm_generator.generatePush("constant","0")
            pass
        vmcode+=self.vm_generator.generateReturn()
        return vmcode

    def processsubroutineCall(self,structure):
        vmcode=""
        dot=structure[1].get("symbol") or structure[1].get("symbol")
        ismethod=False
        if dot==".":
            type=structure[0].get("identifier")
            method=structure[2].get("identifier")
            eli=4
            if self.table.find(type):
                ismethod=True
                segment,num,type=self.table.find(type)
                vmcode+=self.vm_generator.generatePush(segment,num)
        else:
            ismethod=True
            type=self.classname
            method=structure[0].get("identifier")
            vmcode+=self.vm_generator.generatePush("pointer","0")
            eli=2
        
        code,count=self.processexpressionList(structure[eli]["expressionList"])
        vmcode+=code
        numargs=count
        if ismethod:
            numargs+=1
        vmcode+=self.vm_generator.generateCall(type,method,numargs)

        return vmcode

    def processexpressionList(self,structure):
        vmcode=""
        c=0
        for i in range(0,len(structure),2):
            c+=1
            vmcode+=self.processexpression(structure[i]["expression"])

        return [vmcode,c]

    def processterm(self,structure):
        vmcode=""
        key=list(structure[0].keys())[0]
        val=structure[0].get(key)


        if key=="symbol":
            if val=="~":
                vmcode+=self.processterm(structure[1]["term"])
                vmcode+=self.vm_generator.generateArithmetric("not")
            elif val=="-":
                vmcode+=self.processterm(structure[1]["term"])
                vmcode+=self.vm_generator.generateArithmetric("neg")
            elif val=="(":
                vmcode+=self.processexpression(structure[1]["expression"])
        elif key=="identifier":
            key=list(structure[0].keys())[0]
            val=structure[0].get(key)
            val2=""
            if len(structure)>1:
                val2=structure[1].get("symbol")
            if val2=="[":
                segment,num,_=self.table.find(val)
                if self.subroutinefunc=="method" and segment=="argument":
                    num+=1
                vmcode+=self.vm_generator.generatePush(segment,num)
                vmcode+=self.processexpression(structure[2]["expression"])
                vmcode+=self.vm_generator.generateArithmetric("add")
                vmcode+=self.vm_generator.generatePush("pointer","1")
                vmcode+=self.vm_generator.generatePop("temp","1")
                vmcode+=self.vm_generator.generatePop("pointer","1")
                vmcode+=self.vm_generator.generatePush("that","0")
                vmcode+=self.vm_generator.generatePush("temp","1")
                vmcode+=self.vm_generator.generatePop("pointer","1")
            else:
                segment,num,_=self.table.find(val)
                if self.subroutinefunc=="method" and segment=="argument":
                    num+=1
                vmcode+=self.vm_generator.generatePush(segment,num)

        elif key=="integerConstant":
            vmcode+=self.vm_generator.generatePush("constant",val)
        elif key=="stringConstant":
            vmcode+=self.vm_generator.generatePush("constant",len(val[1:-1]))
            vmcode+=self.vm_generator.generateCall("String","new","1")
            vmcode+=self.vm_generator.generatePop("temp", "1")
            for i in val[1:-1]:
                vmcode+=self.vm_generator.generatePush("temp","1")
                vmcode+=self.vm_generator.generatePush("constant",ord(i))
                vmcode+=self.vm_generator.generateCall("String","appendChar","2")
                vmcode+=self.vm_generator.generatePop("temp", "0")
            vmcode+=self.vm_generator.generatePush("temp","1")
        elif key=="subroutineCall":
            vmcode+=self.processsubroutineCall(structure[0]["subroutineCall"])

        elif key=="keyword":
            if val=="true":
                vmcode+=self.vm_generator.generatePush("constant","0")
                vmcode+=self.vm_generator.generatePush("constant","1")
                vmcode+=self.vm_generator.generateArithmetric("sub")
            if val=="false":
                vmcode+=self.vm_generator.generatePush("constant","0")
            if val=="null":
                vmcode+=self.vm_generator.generatePush("constant","0")
            if val=="this":
                vmcode+=self.vm_generator.generatePush("pointer","0")
        elif key=="term":
            vmcode+=self.processterm(structure[0]["term"])
        return vmcode

    def processexpression(self,structure):
        if type(structure)==dict:
            return ""
        vmcode=""
        term=structure[0].get("term")
        op=""
        if len(structure)>1:
            op=structure[1].get("symbol")
            term2=structure[2:]

        opcodes={'+':"add",'-':"sub",'&':"and",'|':"or",'<':"lt",'>':"gt",'=':"eq"}

        vmcode+=self.processterm(term)

        if op:
            vmcode+=self.processterm(term2)
            if op in opcodes:
                vmcode+=self.vm_generator.generateArithmetric(opcodes[op])
            if op in "*":
                vmcode+=self.vm_generator.generateCall("Math","multiply","2")
            if op in "/":
                vmcode+=self.vm_generator.generateCall("Math","divide","2")

        return vmcode