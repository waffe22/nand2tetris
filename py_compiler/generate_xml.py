from html import escape

def generate_xml(tokens,depth=0):
    xml=""
    indent='  '*depth
    if type(tokens)==dict:
        for i,k in tokens.items():
            if type(k)==list:
                xml+=f"{indent}<{i}>\n"
                for j in k:
                    xml+=generate_xml(j,depth+1)
                xml+=f"{indent}</{i}>\n"
            else:
                xml=f"{indent}<{i}>{escape(k)}</{i}>\n"
    elif type(tokens)==list:
        for i in tokens:
            xml+=generate_xml(i,depth+1)
        
    return xml