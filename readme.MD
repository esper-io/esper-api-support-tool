Link to Useage Documentation: https://docs.google.com/document/d/1WwDIQ-7CzQscVNFhiErbYtIwMyE34hGxE_MQWBqc9_k/edit?usp=sharing


Running the executable generator:
    Clone the pyinstaller library (git clone https://github.com/pyinstaller/pyinstaller)
    Follow instructions to build the bootloader: https://pyinstaller.readthedocs.io/en/stable/bootloader-building.html
    Copy the run.exe, run_d.exe, runw.exe, and runw_d.exe files that were genreated (Found in ~\pyinstaller\PyInstaller\bootloader\<platform>)
    Paste files in the pyinstaller site-package (~\AppData\Roaming\Python\Python37\site-packages\PyInstaller\bootloader\<platform>)
        You may want to move/save the exe files that were originally installed
    Run the generateExe.py script