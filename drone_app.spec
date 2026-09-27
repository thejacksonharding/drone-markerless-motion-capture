from pathlib import Path

ROOT = Path(SPECPATH).resolve()
SRC = ROOT / "src"
PKG = SRC / "drone_mocap"

a = Analysis(
    [str(PKG / "run.py")],
    pathex=[str(SRC)],
    excludes=["pytest"],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="drone-mocap",
    console=False,
)

app = BUNDLE(
    exe,
    name="drone-mocap.app",
    bundle_identifier="ca.csialberta.drone-mocap",
)