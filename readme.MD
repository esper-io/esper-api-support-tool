The Esper API Support Tool makes use of Esper’s API to programmatically take control and monitor your Enterprise’s Android-based Dedicated Devices providing features that may not be currently available on the Esper Console Dashboard.


Link to Useage Documentation: https://docs.google.com/document/d/1WwDIQ-7CzQscVNFhiErbYtIwMyE34hGxE_MQWBqc9_k/edit?usp=sharing


Running the executable generator:
        NOTE: For Windows OS users, if you wish to copy the generated exe you may want to use a pyinstaller bootloader that was built locally to avoid anti-virus compliants.
            Clone the pyinstaller library (git clone https://github.com/pyinstaller/pyinstaller)
            Follow instructions to build the bootloader: https://pyinstaller.readthedocs.io/en/stable/bootloader-building.html
            Copy the run.exe, run_d.exe, runw.exe, and runw_d.exe files that were genreated (e.g., Found in ~\pyinstaller\PyInstaller\bootloader\<platform>)
            Paste files in the pyinstaller site-package (e.g., ~\AppData\Roaming\Python\Python37\site-packages\PyInstaller\bootloader\<platform>)
                You may want to move/save the exe files that were originally installed
        Run the generateExe.py script, a executable should be produced in an output folder.
