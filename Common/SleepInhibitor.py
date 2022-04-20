import platform
import Common.Globals as Globals
from subprocess import Popen, PIPE


class SleepInhibitor:
    """Prevent OS sleep/hibernate in windows; code from:
    https://github.com/h3llrais3r/Deluge-PreventSuspendPlus/blob/master/preventsuspendplus/core.py
    API documentation:
    https://msdn.microsoft.com/en-us/library/windows/desktop/aa373208(v=vs.85).aspx"""

    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        self.process = None

    def inhibit(self):
        if platform.system() == "Windows" and Globals.INHIBIT_SLEEP:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(
                SleepInhibitor.ES_CONTINUOUS | SleepInhibitor.ES_SYSTEM_REQUIRED
            )
        elif platform.system() == "Darwin" and Globals.INHIBIT_SLEEP:
            self.process = Popen([u"caffeinate"], stdin=PIPE, stdout=PIPE)

    def uninhibit(self):
        if platform.system() == "Windows" and Globals.INHIBIT_SLEEP:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(SleepInhibitor.ES_CONTINUOUS)
        elif platform.system() == "Darwin" and self.process and Globals.INHIBIT_SLEEP:
            self.process.terminate()
            self.process.wait()
