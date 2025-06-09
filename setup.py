import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "tkinter", "json", "textwrap"],
    "excludes": [],
    "include_files": ["icon.ico"]
}

# GUI applications require a different base on Windows
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Natatnik",
    version="1.0",
    description="Lightweight text editor with basic formatting support",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, target_name="Natatnik.exe", icon="icon.ico")]
)