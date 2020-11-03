import wx
import esperclient
import time
import csv
import os.path
import platform
import logging
import Globals
import platform
import ctypes
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from esperclient import EnterpriseApi, ApiClient
from esperclient.rest import ApiException
from EsperAPICalls import TakeAction


class NewFrameLayout(wx.Frame):
    def __init__(self, *args, **kwds):
        self.configMenuOptions = []
        self.WINDOWS = True
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False
        self.auth_csv_reader = None

        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((1552, 840))
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.configList = wx.TextCtrl(self.panel_3, wx.ID_ANY, "")
        self.combo_box_1 = wx.ComboBox(self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN)
        self.choice_1 = wx.Choice(self.panel_1, wx.ID_ANY, choices=[""])
        self.combo_box_2 = wx.ComboBox(self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN)
        self.button_1 = wx.Button(self.panel_1, wx.ID_ANY, "Run")
        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        self.loggingList = wx.ListBox(self.panel_2, wx.ID_ANY, choices=[""], style=wx.LB_NEEDED_SB)
        
        # Menu Bar
        self.menubar = wx.MenuBar()
        
        fileMenu = wx.Menu()
        fileOpenAuth = fileMenu.Append(wx.ID_OPEN, 'Open Auth CSV', 'Open Auth CSV')
        fileOpenConfig = fileMenu.Append(wx.ID_APPLY, 'Open Device CSV', 'Open Device CSV')
        fileMenu.Append(wx.ID_SEPARATOR)
        fileSave = fileMenu.Append(wx.ID_SAVE, 'Save As', 'Save As')
        fileMenu.Append(wx.ID_SEPARATOR)
        fileItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')

        consoleMenu = wx.Menu()
        clearConsole = consoleMenu.Append(wx.ID_RESET, "Clear", 'Clear Console')

        self.configMenu = wx.Menu()
        self.configMenuOptions.append(self.configMenu.Append(wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"))

        runMenu = wx.Menu()
        run = runMenu.Append(wx.ID_RETRY, "Run", 'Run')

        self.menubar.Append(fileMenu, '&File')
        self.menubar.Append(self.configMenu, '&Configurations')
        self.menubar.Append(consoleMenu, '&Console')
        self.menubar.Append(runMenu, '&Run')
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.OnOpen, fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.onUploadCSV, fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)
        self.Bind(wx.EVT_MENU, self.onSave, fileSave)
        self.Bind(wx.EVT_MENU, self.onClear, clearConsole)
        self.Bind(wx.EVT_MENU, self.onRun, run)
        # Menu Bar end
        
        # Tool Bar
        #self.frame_toolbar = wx.ToolBar(self, -1)
        #self.SetToolBar(self.frame_toolbar)

        #qtool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Quit', png)
        #otool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Open Auth CSV',  wx.Bitmap('Images/openFile.png', wx.BITMAP_TYPE_ANY))
        #stool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Save As',  wx.Bitmap('Images/save.png', wx.BITMAP_TYPE_ANY))
        #ctool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Clear',  wx.Bitmap('Images/clear.png', wx.BITMAP_TYPE_ANY))

        #self.Bind(wx.EVT_TOOL, self.OnQuit, qtool)
        #self.Bind(wx.EVT_TOOL, self.OnOpen, otool)
        #self.Bind(wx.EVT_TOOL, self.onSave, stool)
        #self.Bind(wx.EVT_TOOL, self.onClear, ctool)
        # Tool Bar end

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("frame")
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.choice_1.SetSelection(0)
        #self.frame_toolbar.Realize()
        self.Maximize(True)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_1 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)
        grid_sizer_1 = wx.GridSizer(3, 1, 0, 0)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)
        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Loaded Configuration:", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END)
        label_1.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_1.Wrap(200)
        sizer_2.Add(label_1, 0, wx.EXPAND, 0)
        grid_sizer_3.Add(self.configList, 0, wx.EXPAND, 0)
        self.panel_3.SetSizer(grid_sizer_3)
        sizer_2.Add(self.panel_3, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(sizer_2, 0, wx.EXPAND, 0)
        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Choose the Group to take Action on:", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END)
        label_2.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_3.Add(label_2, 0, wx.EXPAND, 0)
        sizer_3.Add(self.combo_box_1, 0, wx.ALL | wx.EXPAND, 0)
        sizer_3.Add((20, 20), 0, wx.EXPAND, 0)
        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "Action to apply to Devices in Group:", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END)
        label_3.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_3.Add(label_3, 0, wx.EXPAND, 0)
        sizer_3.Add(self.choice_1, 0, wx.EXPAND, 0)
        sizer_3.Add((20, 20), 0, wx.EXPAND, 0)
        label_4 = wx.StaticText(self.panel_1, wx.ID_ANY, "Application for Kiosk Mode", style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END)
        label_4.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_3.Add(label_4, 0, wx.EXPAND, 0)
        sizer_3.Add(self.combo_box_2, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(sizer_3, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.button_1, 0, wx.ALIGN_BOTTOM | wx.EXPAND, 0)
        self.panel_1.SetSizer(grid_sizer_1)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)
        grid_sizer_2.Add(self.loggingList, 0, wx.EXPAND, 0)
        self.panel_2.SetSizer(grid_sizer_2)
        sizer_1.Add(self.panel_2, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def scaleBitmapImage(self, width, height, path):
        image = wx.Bitmap(path).ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        result = wx.Bitmap(image)
        return result

    # Frame UI Logging
    def Logging(self, entry):
        """Logs Infromation To Frame UI"""
        self.loggingList.Append(entry)
        if self.WINDOWS:
            self.loggingList.EnsureVisible(self.loggingList.GetCount() - 1)
        if "--->" not in entry:
            Globals.LOGLIST.append(entry)
        return

    def OnOpen(self, event):
        # otherwise ask the user what new file to open
        with wx.FileDialog(self, "Open Auth CSV File", wildcard="CSV files (*.csv)|*.csv",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            Globals.csv_auth_path = fileDialog.GetPath()
            print(Globals.csv_auth_path)
            self.PopulateConfig()

    def OnQuit(self, e):
        self.Close()

    def askForAuthCSV():
        # Windows, Standalone executable will allow user to select CSV
        if "Windows" in platform.system():
            answer = ctypes.windll.user32.MessageBoxW(
                0, "Please Select The Config CSV", "Esper Tool", 1
            )
            print(answer)
            if answer == 2:
                sys.exit("No CSV Selected")
            root = Tk()
            filename = askopenfilename()
            Globals.csv_auth_path = filename
            print(filename)
            root.destroy()
        # Mac, Debug mode, find csv file using system path
        else:
            currentpath = os.path.realpath(__file__)
            filename = os.path.dirname(currentpath) + os.path.sep + Globals.CONFIGFILE
            Globals.csv_auth_path = filename

    def onSave(self):
        return

    def onClear(self):
        return

    def onUploadCSV(self):
        return

    def onRun(self):
        return

    def PopulateConfig(self):
        """Populates Configuration From CSV"""
        self.Logging("--->Loading Configurations from %s" % Globals.csv_auth_path)
        configfile = Globals.csv_auth_path

        for item in self.configMenuOptions:
            try:
                self.configMenu.Delete(item)
            except:
                pass
        self.configMenuOptions = []

        if os.path.isfile(configfile):
            with open(configfile, newline="") as csvfile:
                self.auth_csv_reader = csv.DictReader(csvfile)
                num = 0
                for row in self.auth_csv_reader:
                    # self.configChoice.Append(row["name"], row)
                    item = self.configMenu.Append(wx.ID_ANY, row["name"], row["name"], kind=wx.ITEM_RADIO)
                    self.Bind(wx.EVT_MENU, self.loadConfiguartion, item)
                    self.configMenuOptions.append(item)
                    if num == 0:
                        wx.Menu().Check(item.Id, False)
                    else:
                        num += 1
        else:
            self.Logging(
                "--->****"
                + Globals.CONFIGFILE
                + " not found - PLEASE Quit and create configuration file"
            )
            self.configMenuOptions.append(self.configMenu.Append(wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"))

    def LoadTagsAndAliases(self):
        return

    def onConfigChoice(self):
        return

    def loadConfiguartion(self, *args, **kwargs):
        """Populate Frame Layout With Device Configuration"""
        choice = self.configChoice.GetSelection()
        selectedConfig = self.configChoice.GetClientData(choice)

        self.configList.Clear()
        self.configList.AppendText("API Host = " + selectedConfig["apiHost"] + "\n")
        self.configList.AppendText("API key = " + selectedConfig["apiKey"] + "\n")
        self.configList.AppendText("API Prefix = " + selectedConfig["apiPrefix"] + "\n")
        self.configList.AppendText("Enterprise = " + selectedConfig["enterprise"])

        if "https" in str(selectedConfig["apiHost"]):
            Globals.configuration.host = selectedConfig["apiHost"]
            Globals.configuration.api_key["Authorization"] = selectedConfig["apiKey"]
            Globals.configuration.api_key_prefix["Authorization"] = selectedConfig[
                "apiPrefix"
            ]
            Globals.enterprise_id = selectedConfig["enterprise"]
            self.PopulateGroups()
            self.PopulateApps()
        else:
            self.Logging(self, "--->**** Please Select an Endpoint")
        return

# end of class MyFrame





class FrameLayout(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(FrameLayout, self).__init__(*args, **kwargs)

        self.WINDOWS = True
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False

        self.configMenuOptions = []

        self.menubar = None
        self.panel = None
        self.configLabel = None
        self.configMenu = None
        self.configList = None
        self.groupLabel = None
        self.groupChoice = None
        self.actionLabel = None
        self.actionChoice = None
        self.appLabel = None
        self.appChoice = None
        self.loggingList = None

        #self.initUI()
    
    def initUI(self):

        # Menu Bar
        

        # Tool Bar
        

        # Body
        self.panel = wx.Panel(self)

        if self.WINDOWS:
            font = wx.Font(
                10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT
            )
        else:
            font = wx.Font(
                14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT
            )
        self.panel.SetFont(font)

        # Configuration UI
        self.configLabel = wx.StaticText(self.panel, label="Loaded Configuration:")
        sizerH.Add(self.configLabel, 1)
        self.configList = wx.TextCtrl(
            self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(200, 80)
        )
        sizerH.Add(self.configList, 1)

        # Action UI
        """
        collpane = wx.CollapsiblePane(self, wx.ID_ANY, "Details:")
        # add the pane with a zero proportion value to the 'sz' sizer which contains it
        sizer.Add(collpane, pos=(2,0), flag=wx.GROW | wx.ALL, border=5)
        # now add a test label in the collapsible pane using a sizer to layout it:
        win = collpane.GetPane()
        paneSz = wx.BoxSizer(wx.VERTICAL)
        paneSz.Add(wx.StaticText(win, wx.ID_ANY, "test!"), 1, wx.GROW | wx.ALL, 2)
        win.SetSizer(paneSz)
        paneSz.SetSizeHints(win)

        self.groupLabel = wx.StaticText(
            self.panel, label="Choose the Group to take Action on"
        )
        sizer.Add(self.groupLabel, pos=(2,0), flag=wx.ALL, border=1)
        self.groupChoice = wx.ComboBox(self.panel, wx.CB_READONLY, size=(100, -1))
        sizer.Add(self.groupChoice, pos=(2,1), flag=wx.ALL, border=5)
        self.actionLabel = wx.StaticText(
            self.panel, label="Action to apply to Devices in Group"
        )
        sizer.Add(self.actionLabel, pos=(3,0), flag=wx.ALL, border=5)
        self.actionChoice = wx.Choice(
            self.panel, wx.CB_SORT, size=(100, -1), choices=Globals.ACTIONS
        )
        sizer.Add(self.actionChoice, pos=(3,1), flag=wx.ALL, border=5)
        self.appLabel = wx.StaticText(self.panel, label="Application for Kiosk Mode")
        sizer.Add(self.appLabel, pos=(4,0), flag=wx.ALL, border=5)
        self.appChoice = wx.ComboBox(self.panel, wx.CB_READONLY, size=(100, -1))
        sizer.Add(self.appChoice, pos=(4,1), flag=wx.ALL, border=5)

        # Logging UI
        if self.WINDOWS:
            self.loggingList = wx.ListBox(self.panel, size=(700, 300))
            myfont = wx.Font(
                8,
                wx.FONTFAMILY_MODERN,
                wx.FONTSTYLE_ITALIC,
                wx.FONTWEIGHT_NORMAL,
                False,
            )
        else:
            self.loggingList = wx.ListBox(self.panel, size=(700, 400))
            myfont = wx.Font(
                10,
                wx.FONTFAMILY_MODERN,
                wx.FONTSTYLE_ITALIC,
                wx.FONTWEIGHT_NORMAL,
                False,
            )
        sizer.Add(self.loggingList, pos=(0,2), flag=wx.ALL, border=5)
        self.loggingList.SetFont(myfont)

        self.panel.SetSizerAndFit(sizer)

        self.SetSizeHints(250, 300, 800, 800)"""
        self.SetSize(800, 800)
        self.SetTitle('Esper API Tool')
        self.Centre()

    