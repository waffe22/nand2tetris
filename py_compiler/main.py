


from .JackTokenizer import *
from .CompilationEngine import *
from .GenerateEngine import *
from .generate_xml import *
from .rule import *
from .SymbolTable import *
from .VMGenerator import *
import pathlib
from pprint import pprint,pformat
import os

def main(jack_dir,os_dir,vm_dir,analytics_dir):

    p=pathlib.Path(jack_dir)
    p2=pathlib.Path(vm_dir)
    p3=pathlib.Path(analytics_dir)
    p4=pathlib.Path(os_dir)

    for path in p2.glob("*"):
        if os.path.isfile(path):
            os.remove(path)
            print(f"removed: {path}")
    for path in p3.glob("*"):
        if os.path.isfile(path):
            os.remove(path)
            print(f"removed: {path}")

    os.makedirs(vm_dir,exist_ok=True)
    os.makedirs(analytics_dir,exist_ok=True)

    for src in p4.glob("*.vm"):
        dst = p2 / src.name
        with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
            fdst.write(fsrc.read())
        print(f"loaded: {src} -> {dst}")


    parser = GrammarParser()
    ruletables = {}
    for name, rule in rules.items():
        ruletables[name] = parser.make_ruletable(rule)
    #pprint(ruletables)

    symbol_table=SymbolTable()
    vm_writer=VMGenerator()

    for jack_path in p.glob("*.jack"):
        name=jack_path.stem
        xml_path=analytics_dir+f"{name}.xml"
        text_path=analytics_dir+f"{name}.py"
        vm_path=vm_dir+f"{name}.vm"
        
        xml_output=open(xml_path,"w",encoding="utf-8")
        vm_output=open(vm_path,"w",encoding="utf-8")
        st_output=open(text_path,"w",encoding="utf-8")

        _input=open(jack_path,"r",encoding="utf-8").read()

        tokens=JackTokenizer(input=_input).tokens
        #print(" ".join(tokens))
        
        compiled_structure=CompilationEngine(tokens,ruletables).run_engine()

        st_output.write(pformat(compiled_structure))

        xml=generate_xml(compiled_structure)
        xml_output.write(xml)

        vm_code=GenerateEngine(symbol_table,vm_writer).engine(compiled_structure)
        vm_output.write(vm_code)

        for i in [xml_path,text_path,vm_path]:
            print(f"created: {i}")