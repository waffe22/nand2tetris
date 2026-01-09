from py_compiler.main import main as run_compiler
from py_vm.main import main as run_vm

jack_dir=r"projects/11/Pong"
analytics_dir=r"out_analytics/"
vm_dir=r"out_vm/"
os_dir=r"os/"
asm_path=r"out_asm/result.asm"

run_compiler(jack_dir,os_dir,vm_dir,analytics_dir)
run_vm(vm_dir,asm_path)
