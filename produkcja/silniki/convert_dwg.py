# -*- coding: utf-8 -*-
"""
Konwersja DWG -> DXF przez GstarCAD w trybie wsadowym (/b skrypt.scr).

Uwaga: pliki "rysunkowe" z systemu klienta bywaja DWG ze zmienionym
rozszerzeniem na .dxf (naglowek binarny 'AC1021' zamiast tekstowego
'0\\nSECTION'). Ta funkcja wykrywa to automatycznie.

Uzycie:
  python convert_dwg.py <plik.dwg|plik.dxf> [plik_wyjsciowy.dxf]
"""
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GCAD = Path(r"C:\Program Files\Gstarsoft\GstarCAD2022\gcad.exe")


def is_real_dxf(path: Path) -> bool:
    """Prawdziwy DXF zaczyna sie tekstem (sekcja '0'), DWG binarnie 'AC10xx'."""
    head = path.read_bytes()[:6]
    return not head.startswith(b"AC10")


def convert(src: Path, dst: Path | None = None, timeout: int = 120) -> Path:
    src = Path(src)
    dst = Path(dst) if dst else src.with_name(src.stem + "_conv.dxf")
    if is_real_dxf(src):
        if src != dst:
            shutil.copy2(src, dst)
        return dst

    # GstarCAD nie lubi UNC -> praca na kopii lokalnej
    work = Path(tempfile.mkdtemp(prefix="dwgconv_"))
    local_dwg = work / (src.stem + ".dwg")
    shutil.copy2(src, local_dwg)
    local_dxf = work / (src.stem + "_conv.dxf")
    scr = work / "conv.scr"
    scr.write_text(
        f'_FILEDIA 0\n_SAVEAS _DXF 16 "{local_dxf}"\n_QUIT _N\n',
        encoding="ascii",
    )
    proc = subprocess.Popen([str(GCAD), str(local_dwg), "/b", str(scr)])
    t0 = time.time()
    while proc.poll() is None:
        if time.time() - t0 > timeout:
            proc.kill()
            raise TimeoutError(f"GstarCAD nie skonczyl w {timeout}s: {src}")
        time.sleep(1)
    if not local_dxf.exists():
        raise RuntimeError(f"Konwersja nie powiodla sie: {src}")
    shutil.copy2(local_dxf, dst)
    shutil.rmtree(work, ignore_errors=True)
    return dst


if __name__ == "__main__":
    out = convert(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(out)
