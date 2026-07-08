# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['1_ASP_Setup.py'],
    pathex=[],
    binaries=[],
    datas=[('Pracownie_ASP_v3.csv', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='awww1(Archiwiktor Wydział Wzornictwa Setup)',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='awww1.ico',
)
app = BUNDLE(
    exe,
    name='awww setup(Archiwiktor Wydział Wzornictwa setup).app',
    icon='awww1.icns',
    bundle_identifier=None,
)
