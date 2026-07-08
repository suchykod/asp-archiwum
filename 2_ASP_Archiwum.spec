# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['awww2(archiwiktor cz.2 kompresja i nazewnictwo).py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    name='awww2(Archiwiktor Wydział Wzornictwa kompresja i nazewnictwo),
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
    icon='awww2.ico',
)
app = BUNDLE(
    exe,
    name='awww2.app',
    icon='awww2.icns',
    bundle_identifier=None,
)
