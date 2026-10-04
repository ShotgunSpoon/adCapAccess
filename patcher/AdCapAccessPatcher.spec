from PyInstaller.utils.hooks import collect_all

ao2_data, ao2_binaries, ao2_hidden = collect_all("accessible_output2")

a = Analysis(
    ["src/patcher.py"],
    pathex=[],
    binaries=ao2_binaries,
    datas=ao2_data + [("readme.txt", ".")],
    hiddenimports=ao2_hidden,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AdCapAccessPatcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
