import re

class JackTokenizer:
    def __init__(self, input: str):
        
        self.tokens = self.tokenize(input)

    def remove_comment(self, s: str):
        s = re.sub(r"//.*", "", s)
        s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
        return s

    def tokenize(self, s: str):
        s=self.remove_comment(s)
        token_pattern = r'''
            "[^"\n]*"                |  # string constant
            \d+                      |  # integer
            [{}()\[\].,;+\-*/&|<>=~] |  # symbol
            [A-Za-z_]\w*                 # identifier / keyword
        '''
        return re.findall(token_pattern, s, re.X)