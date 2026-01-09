from .CodeWriter import CodeWriter
import glob
from .Parser import Parser

def main(vm_dir,asm_path):

    writer=CodeWriter(asm_path)
    t=writer.writeInIt()
    writer.write(t)

    for p in glob.glob(vm_dir+"\*.vm"):

        parser=Parser(p)
        writer.setFileName(p)
        while True:
            if not parser.hasMoreCommands():
                break

            parser.advance()

            type=parser.commandType()

            if type == "C_ARITHMETRIC":
                t=writer.writeArithmetric(parser.arg0())
            if type in ["C_PUSH", "C_POP"]:
                arg1=parser.arg1()
                arg2=parser.arg2()
                t=writer.writePushPop(parser.arg0(),arg1,arg2)
            if type == "C_LABEL":
                t=writer.writeLabel(parser.arg1())
            if type == "C_GOTO":
                arg1=parser.arg1()
                t=writer.writeGoto(arg1)
            if type == "C_IF":
                t=writer.writeIf(parser.arg1())
            if type == "C_FUNCTION":
                t=writer.writeFunction(parser.arg1(),parser.arg2())
            if type == "C_RETURN":
                t=writer.writeReturn()
            if type == "C_CALL":
                t=writer.writeCall(parser.arg1(),parser.arg2())

            writer.write(t)
    writer.close()