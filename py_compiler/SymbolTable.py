


class SymbolTable():
    
    def __init__(self):
        self.field_table={}
        self.var_table={}
        self.arg_table={}
        self.static_table={}

        self.fc=self.vc=self.ac=self.sc=0

    def add(self,scope,type,name):
        if scope=="field":
            self.field_table[name]=["this",self.fc,type]
            self.fc+=1
        if scope=="var":
            self.var_table[name]=["local",self.vc,type]
            self.vc+=1
        if scope=="arg":
            self.arg_table[name]=["argument",self.ac,type]
            self.ac+=1
        if scope=="static":
            self.static_table[name]=["static",self.sc,type]
            self.sc+=1

    def flush(self,scope):
        if scope=="field":
            self.field_table={}
            self.fc=0
        if scope=="var":
            self.var_table={}
            self.vc=0
        if scope=="arg":
            self.arg_table={}
            self.ac=0

    def find(self,name):
        for i,k in self.var_table.items():
            if i==name:
                return k
        for i,k in self.arg_table.items():
            if i==name:
                return k
        for i,k in self.field_table.items():
            if i==name:
                return k
        for i,k in self.static_table.items():
            if i==name:
                return k
            
        return False