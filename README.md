# Natatnik

A lightweight text editor with basic formatting support for Windows.

## Features

- Dark mode interface
- Multiple tabs for editing different files
- Bold text with adjustable font size
- File operations (new, open, save, save as)
- Edit operations (cut, copy, paste)

## Requirements

To build the executable, you need:
- Python 3.6 or higher
- cx_Freeze package (`pip install cx_Freeze`)
- textwrap package (`pip install textwrap`)

## Building the Executable

1. Clone this repository
2. Install the required packages: `pip install cx_Freeze`
3. Run the build command: `python setup.py build`
4. The executable will be created in the `build` directory

## Usage

### Running the Application

- Double-click on `Natatnik.exe` in the build directory
- Alternatively, you can run the Python script directly: `python main.py`

