import os
import wx
import csv
import numpy
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import matplotlib.pyplot as plt

# 1 - Code to grab the data, setup the relevant dictionaries
datafile = "bsubmix10_iso.csv"
picturepath = ""

data = list( csv.reader( open(datafile, 'rU') ) )
header = data[0]

# 1 - Find the indices for the quantities of interest using list comprehensions
UID_index = [index for index, item in enumerate(header) if item == "isofile"][0]
isopep_index = [index for index, item in enumerate(header) if item == "isopep"][0]
protein_index = [index for index, item in enumerate(header) if item == "protein"][0]
isoz_charge_index = [index for index, item in enumerate(header) if item == "isoz_charge"][0]

# the spike defaults to AMP_L, and is only called AMP_S if there are three species
ampu_index = [index for index, item in enumerate(header) if item == "AMP_U"][0]
ampl_index = [index for index, item in enumerate(header) if item == "AMP_L"][0]
amps_index = [index for index, item in enumerate(header) if item == "AMP_S"]
if not amps_index:
    amps_index = ampl_index    
    ampl_index = -1
else:
    amps_index = amps_index[0]
    
N14ppm_index = [index for index, item in enumerate(header) if item == "ppm_n14"][0]
N15ppm_index = [index for index, item in enumerate(header) if item == "ppm_n15"][0]

N14abundance_index = [index for index, item in enumerate(header) if item == "abundance_n14"][0]
N15abundance_index = [index for index, item in enumerate(header) if item == "abundance_n15"][0]

missed_index = [index for index, item in enumerate(header) if item == "missed"][0]

# 2 - Declare the peptide list and the protein set

peptide_list = []
protein_set  = set()
peptide_set = set()

data_dictionary = {}

ppm_difference_list = []
N14ppm_list = []
N15ppm_list = []

csv_hold_dict = {}
UID_list = []
missed_cleavage_list = []

# 3 - Loop over data set, collect amplitudes, charge state, peptide sequence, protein id into protein_set

for line in data[1:]:
	
    ampu = float(line[ampu_index])
    amps = float(line[amps_index])
    if ampl_index == -1:
        ampl = 0
    else:
        ampl = float(line[ampl_index])
    
    isoz_charge = int(line[isoz_charge_index])
    isopep = line[isopep_index]
    protein = line[protein_index]
    N14ppm = float(line[N14ppm_index])
    N15ppm = float(line[N15ppm_index])
    N14abundance = float(line[N14abundance_index])
    N15abundance = float(line[N15abundance_index])
    missed = float(line[missed_index])
    
    UID = line[UID_index]
    csv_hold_dict[UID] = line
    UID_list.append(UID)
    
    identifier = [isopep, isoz_charge, protein, ampu/(ampu+ampl)]

    #######################
    data_dictionary[UID] = {'ampu':ampu, 'ampl':ampl, 'amps':amps, 'N14ppm':N14ppm, 'N15ppm':N15ppm, 
                            'N14abundance':N14abundance, 'N15abundance':N15abundance, 'missed':missed,
                            'isopep':isopep, 'isoz_charge':isoz_charge, 'protein':protein, 'ppmDiff':abs(N14ppm - N15ppm)}
    #######################
    
    ppm_difference_list.append(abs(N14ppm - N15ppm))
    N14ppm_list.append(N14ppm)
    N15ppm_list.append(N15ppm)
    missed_cleavage_list.append(missed)
    
    protein_set.add(protein)
    peptide_set.add(isopep)
    peptide_list.append(identifier)

# 1 - Filtering by ppm high or low on either peak/difference, filtering by abundance high or low
	
for protein in list(protein_set):
    temp_peptides = filter(lambda item: item[2] == protein, peptide_list)
    temp_fraclabs = map(lambda item: item[3], temp_peptides)
    temp_protein = temp_peptides[0][2]

protein_index_dict = { item: index for (index, item) in enumerate(list(protein_set)) }

def outputStatsFile(protein_set, filePrefix, numerator, denominator):
    fileSuffix = "-"
    for i in numerator:
        fileSuffix = fileSuffix+str(i)+"_p_"
    fileSuffix = fileSuffix[:-3]+"_o_"
    for i in denominator:
        fileSuffix = fileSuffix+str(i)+"_p_"
    fileName = filePrefix+fileSuffix[:-3]+".stats"
    outfile = open(fileName, 'w')
    
    outfile.write("Protein flab +\\- loc nval vals\n")

    dataByProtein = {}
    for p in protein_set:
        dataByProtein[p] = {"flab" : -1, "loc" : -1, "nvals" : 0, "vals" : []}
        
    for uid in data_dictionary:
        parentProtein = data_dictionary[uid]['protein']
        value = calcValue(data_dictionary[uid], numerator, denominator)
        dataByProtein[parentProtein]["vals"].append(value)
        dataByProtein[parentProtein]["nvals"] = dataByProtein[parentProtein]["nvals"] + 1
            
    ordered = list(protein_set)
    ordered.sort()
    locIter = 1
    for p in ordered:
        outString = str(p) + " " + str(numpy.mean(dataByProtein[p]["vals"]))[:6] + " " + \
                    str(numpy.std(dataByProtein[p]["vals"]))[:6] + " " + str(locIter) + " " + \
                    str(dataByProtein[p]["nvals"]) + " "
        for v in dataByProtein[p]["vals"]:
            outString = outString + str(v)[:6] + " "    
        outString = outString[:-1] + "\n"
        outfile.write(outString)
    outfile.close()

def calcValue(data, num, den, offset=0.0):
    ns = [data[x] for x in num]
    valNum = reduce(lambda x,y:x+y, ns)
    ds = [data[x] for x in den]
    valDen = reduce(lambda x,y:x+y, ds)
    return float(valNum)/float(valDen) + offset

# 2 - The recommended way to use wx with mpl is with the WXAgg backend. 
class BarsFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'Masse filtering'
    
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)
                
        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()
        
        self.ppmDiffRangeBypass.SetValue('0 100')
        self.N14RangeBypass.SetValue('-100 100')
        self.N15RangeBypass.SetValue('-100 100')
        self.missedRangeBypass.SetValue('0 5')

        self.draw_figure()

    def create_menu(self):
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        
        menu_help = wx.Menu()
        m_about = menu_help.Append(-1, "&About\tF1", "About the demo")
        self.Bind(wx.EVT_MENU, self.on_about, m_about)
        
        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_help, "&Help")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """
        self.panel = wx.Panel(self)
        
        self.fig = Figure((5.0, 4.0))
        self.canvas = FigCanvas(self.panel, -1, self.fig)
        self.axes = self.fig.add_subplot(111)
        
        # Bind the 'pick' event for clicking on one of the bars
        self.canvas.mpl_connect('pick_event', self.on_pick)

        self.ppmDiff_range_button = wx.Button(self.panel, -1, "PPM difference cutoff")
        self.Bind(wx.EVT_BUTTON, self.on_ppmDiff_range_button, self.ppmDiff_range_button)
        
        self.N14_range_button = wx.Button(self.panel, -1, "14N PPM cutoff")
        self.Bind(wx.EVT_BUTTON, self.on_N14_range_button, self.N14_range_button)
        
        self.N15_range_button = wx.Button(self.panel, -1, "15N PPM cutoff")
        self.Bind(wx.EVT_BUTTON, self.on_N15_range_button, self.N15_range_button)
        
        self.missed_range_button = wx.Button(self.panel, -1, "Missed cleavage cutoff")
        self.Bind(wx.EVT_BUTTON, self.on_missed_range_button, self.missed_range_button)
        
############
        
        self.ppmDiffRangeBypass = wx.TextCtrl(
            self.panel, 
            size=(200,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_ppmDiff_range_bypass, self.ppmDiffRangeBypass)
        
        self.N14RangeBypass = wx.TextCtrl(
            self.panel, 
            size=(200,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_N14_range_bypass, self.N14RangeBypass)

        self.N15RangeBypass = wx.TextCtrl(
            self.panel, 
            size=(200,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_N15_range_bypass, self.N15RangeBypass)

        self.missedRangeBypass = wx.TextCtrl(
            self.panel, 
            size=(200,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_missed_range_bypass, self.missedRangeBypass)
        
        
        self.exportButton = wx.Button(self.panel, -1, "Export")
        self.Bind(wx.EVT_BUTTON, self.on_export_button, self.exportButton)
        
        self.drawbutton = wx.Button(self.panel, -1, "Draw!")
        self.Bind(wx.EVT_BUTTON, self.on_draw_button, self.drawbutton)

        self.cb_grid = wx.CheckBox(self.panel, -1, 
            "Show Grid",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)

       # Creates the navigation toolbar
       
        self.toolbar = NavigationToolbar(self.canvas)
        
        # Lays out the various controls
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.toolbar, 0, wx.EXPAND)

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL

        self.hbox.Add(self.drawbutton, 0, border=3, flag=flags)
        self.hbox.Add(self.cb_grid, 0, border=3, flag=flags)
        self.hbox.Add(self.exportButton, 0, border = 3, flag = flags) 
      
        self.vbox.Add(self.hbox, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        
        self.vbox.Add((0,0))
        
        # Sliders for setting the various cutoffs
        self.sliderBox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sliderBox1.Add(self.ppmDiff_range_button, 0, border=3, flag=flags)
        self.sliderBox1.Add(self.ppmDiffRangeBypass, 0, border = 3, flag = flags)

        self.sliderBox1.Add(self.N14_range_button, 0, border=3, flag=flags)
        self.sliderBox1.Add(self.N14RangeBypass, 0, border = 3, flag = flags)
        
        self.vbox.Add(self.sliderBox1, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        
        self.sliderBox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sliderBox2.Add(self.N15_range_button, 0, border=3, flag=flags)
        self.sliderBox2.Add(self.N15RangeBypass, 0, border = 3, flag = flags)

        self.sliderBox2.Add(self.missed_range_button, 0, border=3, flag=flags)
        self.sliderBox2.Add(self.missedRangeBypass, 0, border = 3, flag = flags)        

        self.vbox.Add(self.sliderBox2, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        
    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def draw_figure(self):
        self.UID_output_list = []
        self.axes.clear()
        self.axes.grid(self.cb_grid.IsChecked())
        print "drawing"
        for item in data_dictionary.keys():
            (firstRangeLow, firstRangeHigh) = map(float, self.ppmDiffRangeBypass.GetValue().split(' '))
            (secondRangeLow, secondRangeHigh) = map(float, self.N14RangeBypass.GetValue().split(' '))
            (thirdRangeLow, thirdRangeHigh) = map(float, self.N15RangeBypass.GetValue().split(' '))
            (fourthRangeLow, fourthRangeHigh) = map(float, self.missedRangeBypass.GetValue().split(' '))
            # Test the filter conditions
            con1 = firstRangeLow <= data_dictionary[item]['ppmDiff'] <= firstRangeHigh
            con2 = secondRangeLow <= abs(data_dictionary[item]['N14ppm']) <= secondRangeHigh
            con3 = thirdRangeLow <= abs(data_dictionary[item]['N15ppm']) <= thirdRangeHigh
            con4 = fourthRangeLow <= data_dictionary[item]['missed'] <= fourthRangeHigh
            
            # Keep and plot in black peptides that pass the filters, plot in gray those that do not
            calcNum = ['ampu']
            calcDen = ['amps']
            yval = calcValue(data_dictionary[item], calcNum, calcDen)
            if con1 and con2 and con3 and con4:
                self.axes.plot( protein_index_dict[data_dictionary[item]['protein']], yval, 'kx')
                self.UID_output_list.append(item)
            else:
                self.axes.plot( protein_index_dict[data_dictionary[item]['protein']], yval, 'ro')
        self.axes.set_xlim([0, len(protein_index_dict.items())])
        self.canvas.draw()
        
    def on_export_button(self, event):
        outputStatsFile(protein_set, datafile[0:9], ["ampu"], ["ampl"])
        print 'export complete'
        # Make the list of rejected peptides
        #UID_withheld_list = list(set(UID_list)-set(self.UID_output_list))
        # Clear the output folder and remake it
        #os.system('rm -r output_withheld_pics')
        #os.system('mkdir output_withheld_pics')
        # Copy the fit picture of all rejected peptides to the output folder
        #for item in UID_withheld_list:
            #	os.system('cp '+picturepath+item+'.fit.png '+'output_withheld_pics')
        # Clear the output folder and remake it
        #os.system('rm -r output_pics')
        #os.system('mkdir output_pics')
        # Copy the fit picture of all rejected peptides to the output folder
        #for item in self.UID_output_list:
            #		os.system('cp '+picturepath+item+'.fit.png '+'output_pics')
        #     	print 'export complete'
#     	output_csv = datapath.split('.')[0]+'_filtered.csv'
#     	print output_csv
#     	print csv_hold_dict[self.UID
#     	output_csv_open = open(output_csv, 'w')
#     	for key in self.UID_output_list:
#     		output_csv_open.write(csv_hold_dict[key])
#     	output_csv_open.close()
        #print len(UID_list), len(self.UID_output_list), len(set(UID_list)-set(self.UID_output_list))

    def on_cb_grid(self, event):
        self.draw_figure()
    def on_ppmDiff_range_bypass(self, event):
        pass
    def on_N14_range_bypass(self, event):
        pass
    def on_N15_range_bypass(self, event):
        pass
    def on_missed_range_bypass(self, event):
        pass
    def on_draw_button(self, event):
        self.draw_figure()
    def on_ppmDiff_range_button(self, event):
        app1 = wx.App()
        app1.frame = MyFrame("PPM difference cutoff", ppm_difference_list)
        app1.frame.Show()
        app1.MainLoop()
        
    def on_N14_range_button(self, event):
        app1 = wx.App()
        app1.frame = MyFrame("N14 ppm cutoff", N14ppm_list)
        app1.frame.Show()
        app1.MainLoop()
        
    def on_N15_range_button(self, event):
        app1 = wx.App()
        app1.frame = MyFrame("N15 ppm cutoff", N15ppm_list)
        app1.frame.Show()
        app1.MainLoop()
        
    def on_missed_range_button(self, event):
        app1 = wx.App()
        app1.frame = MyFrame("Missed cleavage cutoff", missed_cleavage_list)
        app1.frame.Show()
        app1.MainLoop()
        
    def on_pick(self, event):
        # The event received here is of the type
        # matplotlib.backend_bases.PickEvent
        #
        # It carries lots of information, of which we're using
        # only a small amount here.
        # 
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on a bar with coords:\n %s" % box_points
        dlg = wx.MessageDialog(
            self, 
            msg, 
            "Click!",
            wx.OK | wx.ICON_INFORMATION)
            
        dlg.ShowModal()
        dlg.Destroy()
        
    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
            
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
            
    def on_exit(self, event):
        self.Destroy()
        
    def on_about(self, event):
        msg = """ A demo using wxPython with matplotlib:
            
        * Use the matplotlib navigation bar
        * Add values to the text box and press Enter (or click "Draw!")
        * Show or hide the grid
        * Drag the slider to modify the width of the bars
        * Save the plot to a file using the File menu
        * Click on a bar to receive an informative message
        """
        
        dlg = wx.MessageDialog(self, msg, "About", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER, 
            self.on_flash_status_off, 
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)
        
    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')
        
# Second window popup for graphs

class MyFrame(wx.Frame):
    def __init__(self, passed_title, passed_data):
        self.title = passed_title
        self.data = passed_data
        
        wx.Frame.__init__(self, None, -1, self.title)
        
        self.create_main_panel()
        self.draw_figure(self.data)
        
    def create_main_panel(self):
        """ Creates the main panel with all the controls on it:
            * mpl canvas 
            * mpl navigation toolbar
            * Control panel for interaction"""
        self.panel = wx.Panel(self)
        self.fig = Figure((5.0, 4.0))
        self.canvas = FigCanvas(self.panel, -1, self.fig)		
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add((0,0))
        self.vbox.Fit(self)
        self.axes = self.fig.add_subplot(111)
        
    def draw_figure(self, thing):
        bin_num = min(80, len(list(set(thing))))
        self.axes.hist(thing, bins = bin_num)
        self.canvas.draw()

if __name__ == '__main__':
#        outputStatsFile(protein_set, datafile[0:9], ["ampu", "amps"], ["ampl", "ampu", "amps"])
#        print 'export complete'
    app = wx.App()
    app.frame = BarsFrame()
    app.frame.Show()
    app.MainLoop()