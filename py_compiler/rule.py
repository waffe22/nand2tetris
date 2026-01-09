import re

rules = {
    "class":
        "'class' className '{' classVarDec* subroutineDec* '}'",

    "classVarDec":
        "('static' | 'field') ('int' | 'char' | 'boolean' | className) "
        "varName (',' varName)* ';'",

    "subroutineDec":
        "('constructor' | 'function' | 'method') "
        "('void' | 'int' | 'char' | 'boolean' | className) subroutineName "
        "'(' parameterList ')' subroutineBody",

    "parameterList":
        "((('int' | 'char' | 'boolean' | className) varName) "
        " (',' ('int' | 'char' | 'boolean' | className) varName)*)?",

    "subroutineBody":
        "'{' varDec* statements '}'",

    "varDec":
        "'var' ('int' | 'char' | 'boolean' | className) varName (',' varName)* ';'",

    "statements":
        "(letStatement | ifStatement | whileStatement | doStatement | returnStatement)*",

    "letStatement":
        "'let' varName ('[' expression ']')? '=' expression ';'",

    "ifStatement":
        "'if' '(' expression ')' '{' statements '}' "
        "('else' '{' statements '}')?",

    "whileStatement":
        "'while' '(' expression ')' '{' statements '}'",

    "doStatement":
        "'do' subroutineCall ';'",

    "returnStatement":
        "'return' expression? ';'",

    "expression":
        "term (('+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=') term)*",

    "term":
        "integerConstant | stringConstant | "
        "('true' | 'false' | 'null' | 'this') | "
        "varName '[' expression ']' | "
        "subroutineCall | '(' expression ')' | "
        "('-' | '~') term | varName",

    "subroutineCall":
        "subroutineName '(' expressionList ')' | "
        "(className | varName) '.' subroutineName '(' expressionList ')'",

    "expressionList":
        "(expression (',' expression)*)?"
}

class GrammarParser:
    def __init__(self):
        pass

    def tokenize(self, rule):
        token_pattern = r"""
            '[^']+' |        # 'class'
            \(|\)|\*|\?|\| | # symbols
            [A-Za-z_]\w*     # identifiers
        """
        return re.findall(token_pattern, rule, re.VERBOSE)
    

    def parse(self, tokens):
        result = []
        orflag=False
        orcount=0
        while tokens:
            tok = tokens.pop(0)

            if tok == "(":
                node = self.parse(tokens)
                result.append(node)
                continue

            elif tok == ")":
                break

            if tok == "|":

                if result:
                    a=result[orcount:]
                    result=result[:orcount]
                    result.append({
                    "a": "&",
                    "c": a
                    })
                orflag=True
                orcount+=1


            elif tok in ("*", "?"):
                result[-1] = {
                    "a": tok,
                    "c": [result[-1]]
                }

            else:
                result.append(tok)

        if not orflag:
            return {
                "a": "&",
                "c": result
            }
        else:
            a=result[orcount:]
            result=result[:orcount]
            result.append({
            "a": "&",
            "c": a
            })
            return {
                "a": "|",
                "c": result
            }

    def make_ruletable(self, rule):
        tokens = self.tokenize(rule)
        tree = self.parse(tokens)

        if tree["a"] == "&":
            return {"a": "&","c": tree["c"]}
        else:
            return {"a": "&","c": [tree]}

if __name__=="__main__":
    parser = GrammarParser()
    ruletables = {}

    for name, rule in rules.items():
        ruletables[name] = parser.make_ruletable(rule)

    from pprint import pprint
    pprint(ruletables)