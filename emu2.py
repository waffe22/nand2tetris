

from typing import List, Callable, Optional
import numpy as np
import pygame
import time,threading


running = True
MASK16 = 0xFFFF
emu=None

def u16(x: int) -> int:
    return x & MASK16

def s16(x: int) -> int:
    x &= MASK16
    return x - 0x10000 if x & 0x8000 else x

# -------------------------
# 命令クラス（軽量）
# -------------------------
class AInst:
    __slots__ = ("v",)
    def __init__(self, v:int): self.v = int(v)

class CInst:
    __slots__ = ("writeA","writeD","writeM","comp_fn","jump_fn","raw")
    def __init__(self, wa, wd, wm, comp_fn, jump_fn, raw=""):
        self.writeA = wa
        self.writeD = wd
        self.writeM = wm
        self.comp_fn = comp_fn
        self.jump_fn = jump_fn
        self.raw = raw

# -------------------------
# comp テーブル (完全)
# -------------------------
def make_comp_table():
    # すべて signed 16bit 値で演算し最終的に u16 を戻す
    def U(x): return u16(x)
    def S(x): return s16(x)
    t = {}
    # constants
    t["0"]   = lambda A,D,M: U(0)
    t["1"]   = lambda A,D,M: U(1)
    t["-1"]  = lambda A,D,M: U(-1)
    # registers
    t["D"]   = lambda A,D,M: U(D)
    t["A"]   = lambda A,D,M: U(A)
    t["M"]   = lambda A,D,M: U(M)
    # not
    t["!D"]  = lambda A,D,M: U(~S(D))
    t["!A"]  = lambda A,D,M: U(~S(A))
    t["!M"]  = lambda A,D,M: U(~S(M))
    # neg
    t["-D"]  = lambda A,D,M: U(-S(D))
    t["-A"]  = lambda A,D,M: U(-S(A))
    t["-M"]  = lambda A,D,M: U(-S(M))
    # +/-1
    t["D+1"] = lambda A,D,M: U(S(D)+1)
    t["A+1"] = lambda A,D,M: U(S(A)+1)
    t["M+1"] = lambda A,D,M: U(S(M)+1)
    t["D-1"] = lambda A,D,M: U(S(D)-1)
    t["A-1"] = lambda A,D,M: U(S(A)-1)
    t["M-1"] = lambda A,D,M: U(S(M)-1)
    # arithmetic
    t["D+A"] = lambda A,D,M: U(S(D)+S(A))
    t["A+D"] = t["D+A"]
    t["D+M"] = lambda A,D,M: U(S(D)+S(M))
    t["M+D"] = t["D+M"]
    t["D-A"] = lambda A,D,M: U(S(D)-S(A))
    t["D-M"] = lambda A,D,M: U(S(D)-S(M))
    t["A-D"] = lambda A,D,M: U(S(A)-S(D))
    t["M-D"] = lambda A,D,M: U(S(M)-S(D))
    # bitwise
    t["D&A"] = lambda A,D,M: U(S(D) & S(A))
    t["A&D"] = t["D&A"]
    t["D&M"] = lambda A,D,M: U(S(D) & S(M))
    t["M&D"] = t["D&M"]
    t["D|A"] = lambda A,D,M: U(S(D) | S(A))
    t["A|D"] = t["D|A"]
    t["D|M"] = lambda A,D,M: U(S(D) | S(M))
    t["M|D"] = t["D|M"]
    # also support single-letter forms like "A" handled above
    return t

COMP_TABLE = make_comp_table()

def make_jump_fn(jmp: Optional[str]) -> Optional[Callable[[int], bool]]:
    if not jmp: return None
    if jmp == "JGT": return lambda v: s16(v) > 0
    if jmp == "JEQ": return lambda v: s16(v) == 0
    if jmp == "JGE": return lambda v: s16(v) >= 0
    if jmp == "JLT": return lambda v: s16(v) < 0
    if jmp == "JNE": return lambda v: s16(v) != 0
    if jmp == "JLE": return lambda v: s16(v) <= 0
    if jmp == "JMP": return lambda v: True
    return None

# -------------------------
# ASM -> ROM コンパイラ（2パス）
# -------------------------
SYMBOLS_BASE = { **{f"R{i}": i for i in range(16)},
                 "SP":0,"LCL":1,"ARG":2,"THIS":3,"THAT":4,
                 "SCREEN":16384, "KBD":24576 }

def compile_asm_lines(lines: List[str]):
    # lines: raw lines (may contain comments). returns list of AInst/CInst
    # 1) clean and first pass labels
    cleaned = []
    sym = dict(SYMBOLS_BASE)
    pc = 0
    for r in lines:
        s = r.split("//")[0].strip()
        if not s: continue
        if s.startswith("(") and s.endswith(")"):
            label = s[1:-1]
            if label not in sym:
                sym[label] = pc
        else:
            cleaned.append(s)
            pc += 1
    # 2) variables and compile
    next_var = 16
    ROM = []
    for s in cleaned:
        if s.startswith("@"):
            tok = s[1:]
            if tok.isdigit():
                v = int(tok)
            else:
                if tok not in sym:
                    sym[tok] = next_var
                    next_var += 1
                v = sym[tok]
            ROM.append(AInst(v & MASK16))
        else:
            # C-instruction: dest=comp;jump (dest or jump may be absent)
            dest = None
            comp = None
            jump = None
            part = s
            if ";" in part:
                part, jump = part.split(";",1)
                jump = jump.strip()
            if "=" in part:
                dest, comp = part.split("=",1)
                dest = dest.strip()
                comp = comp.strip()
            else:
                comp = part.strip()
            comp_n = comp.replace(" ", "")
            if comp_n not in COMP_TABLE:
                raise ValueError(f"Unknown comp mnemonic: {comp_n}")
            comp_fn = COMP_TABLE[comp_n]
            jfn = make_jump_fn(jump)
            wa = ("A" in dest) if dest else False
            wd = ("D" in dest) if dest else False
            wm = ("M" in dest) if dest else False
            ROM.append(CInst(wa, wd, wm, comp_fn, jfn, raw=comp_n))
    return ROM

# -------------------------
# 高速エミュレータ本体
# -------------------------
class FastEmu:
    def __init__(self, rom: List, mem_size:int=32768):
        self.ROM = rom
        self.mem = [0]*mem_size   # list[int], 16bit words
        self.A = 0
        self.D = 0
        self.PC = 0

    def step(self) -> bool:
        pc = self.PC
        rom = self.ROM
        if pc < 0 or pc >= len(rom):
            return False
        inst = rom[pc]
        # A instruction
        if isinstance(inst, AInst):
            self.A = inst.v & MASK16
            self.PC = pc + 1
            return True
        # C instruction
        # localize for speed
        A = self.A
        D = self.D
        M = self.mem[A]  # stored as unsigned 16
        # comp_fn expects (A,D,M) as ints (works with unsigned or signed conversions inside)
        v_u = inst.comp_fn(A, D, M)
        # write destinations
        if inst.writeA:
            self.A = v_u & MASK16
        if inst.writeD:
            # store as signed-ish? we keep python int; D used in comp as int
            # store raw unsigned 16 to keep consistent
            self.D = s16(v_u)
        if inst.writeM:
            self.mem[A] = v_u & MASK16
        # jump
        if inst.jump_fn and inst.jump_fn(v_u):
            self.PC = self.A
        else:
            # if jump exists but false, increment; if no jump, increment
            if not inst.jump_fn:
                self.PC = pc + 1
            else:
                self.PC = pc + 1
        return True

    def run(self, max_steps:Optional[int]=None):
        i = 0
        while True:
            if max_steps is not None and i >= max_steps:
                break
            ok = self.step()
            if not ok:
                break
            i += 1
        return i

# -------------------------
# 画面変換 (memory -> frame 256x512) : NumPy vectorized
# -------------------------
def convert_screen(memory_list: List[int]) -> np.ndarray:
    """
    memory_list : 16bit ワードのリスト（長さ 24576 以上）
    戻り値：uint8(0/1) の画面配列 shape=(256,512)
    """
    base = 16384
    H, W = 256, 512

    # memory_list を numpy 配列化（16bit ワード）
    memarr = np.asarray(memory_list, dtype=np.uint16)

    # r: 行 0〜255, c:列 0〜511
    r = np.arange(H, dtype=np.int32).reshape(H, 1)
    c = np.arange(W, dtype=np.int32).reshape(1, W)

    # アドレス計算
    addr = base + r * 32 + (c // 16)        # shape=(256,512)

    # bit マスク (左＝MSB が bit15)
    bit = c % 16                     # shape=(256,512)

    # ワードをロード
    words = memarr[addr]                    # shape=(256,512)

    # 各ビットを取り出す
    frame = ((words >> bit) & 1).astype(np.uint8)

    return frame



def array_to_surface(img01: np.ndarray):
    # img01: (H, W) 0/1 uint8
    # convert to 3-channel 0..255 and make surface
    # pygame.surfarray.make_surface expects (W,H,3) with dtype uint8
    img8 = (img01.astype(np.uint8) * 255)
    # stack to RGB (H,W,3)
    rgb = np.stack([~img8, ~img8, ~img8], axis=2)
    # pygame wants (width, height) orientation for surfarray.make_surface: pass transposed
    surf = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
    return surf


def run_monitor():
    global running,emu
    W, H = 512,256
    FPS = 60
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()
    
    img01 = convert_screen(emu.mem)

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False
        try:
            img01 = convert_screen(emu.mem)
        except:
            pass
        surf = array_to_surface(img01)

        screen.blit(surf, (0, 0))
        pygame.display.flip()

        # cap framerate to 30 FPS
        clock.tick(FPS)

    pygame.quit()


def run_keyboard():
    global running, emu

    while running:
        keys = pygame.key.get_pressed()

        key_state = 0
        if keys[pygame.K_RETURN]: key_state = 128
        if keys[pygame.K_BACKSPACE]: key_state = 129
        if keys[pygame.K_LEFT]: key_state = 130
        if keys[pygame.K_UP]: key_state = 131
        if keys[pygame.K_RIGHT]: key_state = 132
        if keys[pygame.K_DOWN]: key_state = 133
        if keys[pygame.K_HOME]: key_state = 134
        if keys[pygame.K_END]: key_state = 135
        if keys[pygame.K_PAGEUP]: key_state = 136
        if keys[pygame.K_PAGEDOWN]: key_state = 137
        if keys[pygame.K_INSERT]: key_state = 138
        if keys[pygame.K_DELETE]: key_state = 139
        if keys[pygame.K_ESCAPE]: key_state = 140

        # ASCII
        for i in range(0x21, 0x7f):
            if keys[i]:
                key_state = i

        emu.mem[24576] = key_state
        time.sleep(0.005)

# -------------------------
# ユーティリティ: ファイル読み込み
# -------------------------
def load_asm(path:str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()

# -------------------------
# 簡単な使用例
# -------------------------
if __name__ == "__main__":
    # 例: Pong.asm のパスに合わせて読み込む
    asm_path = r"Pong.asm"   # 適宜変更
    lines = load_asm(asm_path)
    ROM = compile_asm_lines(lines)
    emu = FastEmu(ROM)

    t = threading.Thread(target=run_monitor, args=())
    t.start()
    t2 = threading.Thread(target=run_keyboard, args=())
    t2.start()
    
    try:
        while True:
            emu.run(10000)
            time.sleep(0.0001)
    except KeyboardInterrupt:
        running=False