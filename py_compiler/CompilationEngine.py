


class CompilationEngine():
    def __init__(self,tokens,ruletables):

        self.tokens=tokens
        self.ruletables=ruletables
        self.pointer=0
        
    def check(self,token,expect_token):
        #print(token,expect_token)
        if expect_token[0]==expect_token[-1]=="'":
            expect_token=expect_token[1:-1]
            return expect_token==token
        
        symbols=["{","}","(",")","[","]",".",",",";","+","-","*","/","&",
                 "|","<",">","=","~"]
        isidentifier=lambda x:x[0].isascii() and not x[0].isnumeric() and not any([s in x for s in symbols])
        if expect_token in ["className","varName","subroutineName"]:
            return isidentifier(token)
        else:
            return self.tokenType(token)==expect_token

    def tokenType(self,token):

        keywords=["class","constructor","function","method",
                 "field","static","var","int","char","boolean","void",
                 "true","false","null","this",
                 "let","do","if","else","while","return"]
        symbols=["{","}","(",")","[","]",".",",",";","+","-","*","/","&",
                 "|","<",">","=","~"]
        isintegerConstant=lambda x:x.isnumeric()
        isstringConstant=lambda x:x[0]==x[-1]=="\""
        isidentifier=lambda x:x[0].isascii() and not x[0].isnumeric() and \
        not any([s in x for s in symbols])

        if token in keywords:
            return "keyword"
        elif token in symbols:
            return "symbol"
        elif isintegerConstant(token):
            return "integerConstant"
        elif isstringConstant(token):
            return "stringConstant"
        elif isidentifier(token):
            return "identifier"
        
    def run_engine(self,index=["class"]):
        ruletable=self.ruletables.copy()
        #print(index)
        for i in index:
            ruletable=ruletable[i]
        appear=ruletable["a"]
        find_tokens=[]
        for i,t in enumerate(ruletable["c"]):
            if type(t)==str:
                if t in self.ruletables:
                    save_pointer=self.pointer
                    a=self.run_engine(index=[t])
                    if not a==False:#
                        find_tokens.append({t:a})
                        if appear=="|":
                            return find_tokens
                        continue
                    else:#
                        self.pointer=save_pointer
                        if appear=="|":
                            if i==len(ruletable["c"])-1:
                                return False
                            else:
                                continue
                        return False
                else:
                    a=self.check(token=self.tokens[self.pointer],expect_token=t)
                    if not a==False:#
                        find_tokens.append({self.tokenType(self.tokens[self.pointer]):self.tokens[self.pointer]})
                        self.pointer+=1
                        if appear=="|":
                            return True
                        continue
                    else:#
                        if appear=="|":
                            if i==len(ruletable["c"])-1:
                                return False
                            else:
                                continue
                        return False
            elif type(t)==dict:
                appear2=t["a"]
                save_pointer=self.pointer
                a=self.run_engine(index=index+["c",i])
                if not a==False:#
                    find_tokens.extend(a)
                    if appear=="|":
                        return find_tokens
                    continue
                else:#
                    self.pointer=save_pointer
                    if appear=="|":
                        if i==len(ruletable["c"])-1:
                            return False
                        else:
                            continue
                    if appear2 in "*?":
                        continue
                    else:
                        return False
        if appear=="*":
            a=self.run_engine(index=index)
            if not a==False:
                find_tokens.extend(a)
        

        if index==["class"]:
            return {"class":find_tokens}
        else:
            return find_tokens
