import os
import wx
import qMS
import qMSDefs
import string
import pylab
import csv
import pandas as pd
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar

class MasseFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'Masse filtering'
    
    def __init__(self, df, dp, fn, ci, pulse=False, varLab=False):
        wx.Frame.__init__(self, None, -1, self.title)                
        self.create_main_panel(pulse=pulse, varLab=varLab)

        self.calcNum = ["AMP_U"]
        self.calcDen = ["AMP_U", "AMP_S"]
        self.currentHist = "ppmDiff"
        self.positionLabels = qMSDefs.positionLabels70S
        self.currentDirectory = os.getcwd()
        self.dataFrame = df
        self.datapath = dp
        self.datafile = fn
        self.currentISOFile = ci
        
        self.lowCheckNum.SetValue(True)
        self.lowCheckDen.SetValue(True)
        self.highCheckDen.SetValue(True)
        self.ppmDiffRangeBypass.SetValue('-100 100')
        self.N14RangeBypass.SetValue('-100 100')
        self.N15RangeBypass.SetValue('-100 100')
        self.missedRangeBypass.SetValue('0 5')        
        self.rtDiffRangeBypass.SetValue('-0.5 0.5')
        self.residRangeBypass.SetValue('0 5000')

        self.ppmDiffOn.SetValue(True)
        self.N14On.SetValue(True)
        self.N15On.SetValue(True)
        self.missedOn.SetValue(True)
        self.rtOn.SetValue(True)
        self.residOn.SetValue(True)
        
        if varLab:
            self.FRC_NXRangeBypass.SetValue('0 1')
            self.FRC_NXOn.SetValue(True)
        
        self.calc_fit()
        self.calc_figure()
        self.calc_hist()
        self.draw_all()

    def create_main_panel(self, pulse=False, varLab=False):
        """ Creates the main panel with all the controls on it:
             * mpl canvas 
             * mpl navigation toolbar
             * Control panel for interaction
        """
        self.panel = wx.Panel(self)
        
        '''Create the figure panels'''
        self.figLeft = Figure((7.5, 7.5))
        self.canvasLeft = FigCanvas(self.panel, wx.ID_ANY, self.figLeft)
        self.figRight = Figure((7.5, 7.5))
        self.canvasRight = FigCanvas(self.panel, wx.ID_ANY, self.figRight)
        
        gsLeft = gridspec.GridSpec(5,1)
        gsRight = gridspec.GridSpec(5,1)
        self.PLPlot = self.figLeft.add_subplot(gsLeft[:4, :])
        self.PNGPlot = self.figRight.add_subplot(gsRight[:4, :])
        
        self.histPlotAll = self.figLeft.add_subplot(gsLeft[4, :])
        self.histPlotSelected = self.figRight.add_subplot(gsRight[4, :])
        self.figLeft.tight_layout()
        self.figRight.tight_layout()
        
        '''Create the list boxes'''
        #self.time_zones = wx.ListBox(panel, 26, wx.DefaultPosition, (170, 130), zone_list, wx.LB_SINGLE)
        #self.time_zones.SetSelection(0)
        
        '''Create the buttons'''
        self.toolbar = NavigationToolbar(self.canvasLeft)
        
        self.cb_grid = wx.CheckBox(self.panel, wx.ID_ANY, label="Show Grid", style=wx.ALIGN_RIGHT)        
        self.drawButton = wx.Button(self.panel, wx.ID_ANY, "Draw!")
        self.exportButton = wx.Button(self.panel, wx.ID_ANY, "Export")
        self.openButton = wx.Button(self.panel, wx.ID_ANY, "Open")
        
        self.r70S = wx.RadioButton(self.panel, label="70S", style=wx.RB_GROUP)
        self.r50S = wx.RadioButton(self.panel, label="50S")
        self.r30S = wx.RadioButton(self.panel, label="30S")
        
        self.savePButton = wx.Button(self.panel, wx.ID_ANY, "Save")
        self.loadPButton = wx.Button(self.panel, wx.ID_ANY, "Load")
        
        self.calcButton = wx.Button(self.panel, wx.ID_ANY, "Calculate")
        
        self.lowCheckNum = wx.CheckBox(self.panel, wx.ID_ANY, label="low")
        if pulse:
            self.midCheckNum = wx.CheckBox(self.panel, wx.ID_ANY, label="mid")
        self.highCheckNum = wx.CheckBox(self.panel, wx.ID_ANY, label="high")
        
        self.lowCheckDen = wx.CheckBox(self.panel, wx.ID_ANY, label="low")
        if pulse:
            self.midCheckDen = wx.CheckBox(self.panel, wx.ID_ANY, label="mid")
        self.highCheckDen = wx.CheckBox(self.panel, wx.ID_ANY, label="high")

        self.ppmDiff_range_button = wx.Button(self.panel, wx.ID_ANY, "PPM difference cutoff")        
        self.N14_range_button = wx.Button(self.panel, wx.ID_ANY, "14N PPM cutoff")        
        self.N15_range_button = wx.Button(self.panel, wx.ID_ANY, "15N PPM cutoff")
        self.missed_range_button = wx.Button(self.panel, wx.ID_ANY, "Missed cleavage cutoff")
        self.rtDiff_range_button = wx.Button(self.panel, wx.ID_ANY, "RT diff cutoff")
        self.resid_range_button = wx.Button(self.panel, wx.ID_ANY, "residual cutoff")
        if varLab:
            self.FRC_NX_range_button = wx.Button(self.panel, wx.ID_ANY, "FRC_NX")
        
        self.ppmDiffRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.N14RangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.N15RangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.missedRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.rtDiffRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.residRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        if varLab:
            self.FRC_NXRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)

        self.ppmDiffOn = wx.CheckBox(self.panel, wx.ID_ANY, label="ppmDiff")
        self.N14On = wx.CheckBox(self.panel, wx.ID_ANY, label="N14")
        self.N15On = wx.CheckBox(self.panel, wx.ID_ANY, label="N15")
        self.missedOn = wx.CheckBox(self.panel, wx.ID_ANY, label="missed")
        self.rtOn = wx.CheckBox(self.panel, wx.ID_ANY, label="RTDiff")
        self.residOn = wx.CheckBox(self.panel, wx.ID_ANY, label="residuals")
        if varLab:
            self.FRC_NXOn = wx.CheckBox(self.panel, wx.ID_ANY, label="FRC_NX")
        

        '''lay out the buttons'''
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.figbox = wx.BoxSizer(wx.HORIZONTAL)
        self.figbox.Add(self.canvasLeft, 0)
        self.figbox.Add(wx.BoxSizer(wx.HORIZONTAL), 1, flag=wx.GROW)
        self.figbox.Add(self.canvasRight, 0)
        self.vbox.Add(self.figbox, 0, flag = wx.GROW)

        #new horizontal box    
        self.toolNumBox = wx.BoxSizer(wx.HORIZONTAL)
        
        #add toolbar, draw, grid and exportto hbox
        self.imageToolsBox = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'image tools'), wx.HORIZONTAL)
        self.imageToolsBox.Add(self.toolbar, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.imageToolsBox.Add(self.cb_grid, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.imageToolsBox.Add(self.drawButton, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.toolNumBox.Add(self.imageToolsBox, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)

        #add open and export buttons
        self.fileToolsBox = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'file tools'), wx.HORIZONTAL)
        self.fileToolsBox.Add(self.openButton, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.fileToolsBox.Add(self.exportButton, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)        
        self.toolNumBox.Add(self.fileToolsBox, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        
        #add subunit radio buttons to hbox
        self.subunitBox = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'displaySubunits'), wx.HORIZONTAL)
        self.subunitBox.Add(self.r70S, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.subunitBox.Add(self.r50S, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.subunitBox.Add(self.r30S, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.toolNumBox.Add(self.subunitBox, 0, flag=wx.ALIGN_LEFT | wx.GROW)
        self.toolNumBox.Add(wx.BoxSizer(wx.HORIZONTAL), 1, flag=wx.GROW) #push all remaining to the right
        
        #add loadP/SaveP buttons
        self.paramBox = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'filterParamters'), wx.HORIZONTAL)
        self.paramBox.Add(self.savePButton, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.paramBox.Add(self.loadPButton, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.toolNumBox.Add(self.paramBox, 0, flag=wx.ALIGN_RIGHT | wx.GROW)
        
        #add calculate button
        self.toolNumBox.Add(self.calcButton, 0, flag=wx.ALIGN_RIGHT | wx.GROW)
        
        #add numerator box to hbox
        self.numBox = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'numerator'), wx.HORIZONTAL)
        self.numBox.Add(self.lowCheckNum, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        if pulse:
            self.numBox.Add(self.midCheckNum, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.numBox.Add(self.highCheckNum, 0,flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.toolNumBox.Add(self.numBox, 0, flag=wx.ALIGN_RIGHT | wx.GROW)
        #add denominator box to hbox
        self.denBox = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'denominator'), wx.HORIZONTAL)
        self.denBox.Add(self.lowCheckDen, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        if pulse:
            self.denBox.Add(self.midCheckDen, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.denBox.Add(self.highCheckDen, 0,flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.toolNumBox.Add(self.denBox, 0, flag=wx.ALIGN_RIGHT | wx.GROW)
        
        #add hbox to vbox
        self.vbox.Add(self.toolNumBox, 0, flag = wx.GROW)
        
        # Sliders for setting the various cutoffs
        self.filterBox = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'filter settings'), wx.HORIZONTAL)
        flags = wx.ALIGN_LEFT | wx.ALIGN_CENTER
        self.filterBox.Add(self.ppmDiff_range_button, 0, flag=flags)
        self.filterBox.Add(self.ppmDiffRangeBypass, 0, flag=flags)
        self.filterBox.Add(self.N14_range_button, 0, flag=flags)
        self.filterBox.Add(self.N14RangeBypass, 0, flag=flags)
        self.filterBox.Add(self.N15_range_button, 0, flag=flags)
        self.filterBox.Add(self.N15RangeBypass, 0, flag = flags)
        self.filterBox.Add(self.missed_range_button, 0, flag=flags)
        self.filterBox.Add(self.missedRangeBypass, 0, flag = flags)
        self.filterBox.Add(self.rtDiff_range_button, 0, flag=flags)
        self.filterBox.Add(self.rtDiffRangeBypass, 0, flag = flags)
        if varLab:
            self.filterBox.Add(self.FRC_NX_range_button, 0, flag=flags)
            self.filterBox.Add(self.FRC_NXRangeBypass, 0, flag = flags)
        self.filterBox.Add(self.resid_range_button, 0, flag=flags)
        self.filterBox.Add(self.residRangeBypass, 0, flag = flags)
        self.vbox.Add(self.filterBox, 0, flag = wx.ALIGN_LEFT | wx.TOP)
        
        # Filters on/off checks
        self.controlFilters = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'filter on/off'), wx.HORIZONTAL)
        self.controlFilters.Add(self.ppmDiffOn, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.controlFilters.Add(self.N14On, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.controlFilters.Add(self.N15On, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.controlFilters.Add(self.missedOn, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.controlFilters.Add(self.rtOn, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.controlFilters.Add(self.residOn, 0, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        if varLab:
            self.controlFilters.Add(self.FRC_NXOn, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
        self.vbox.Add(self.controlFilters, 0, flag = wx.ALIGN_LEFT | wx.TOP)

        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        
        '''bind events for buttons'''
        self.canvasLeft.mpl_connect('pick_event', self.on_pick)
        self.r70S.Bind(wx.EVT_RADIOBUTTON, self.onr70S_select)
        self.r50S.Bind(wx.EVT_RADIOBUTTON, self.onr50S_select)
        self.r30S.Bind(wx.EVT_RADIOBUTTON, self.onr30S_select)

        self.drawButton.Bind(wx.EVT_BUTTON, self.on_draw_button)
        self.exportButton.Bind(wx.EVT_BUTTON, self.on_export_button)
        self.openButton.Bind(wx.EVT_BUTTON, self.on_open_button)
        self.calcButton.Bind(wx.EVT_BUTTON, self.on_calc_button)
        self.cb_grid.Bind(wx.EVT_CHECKBOX, self.on_cb_grid)
        
        self.loadPButton.Bind(wx.EVT_BUTTON, self.on_loadP_button)
        self.savePButton.Bind(wx.EVT_BUTTON, self.on_saveP_button)

        self.ppmDiff_range_button.Bind(wx.EVT_BUTTON, self.on_ppmDiff_range_button)
        self.N14_range_button.Bind(wx.EVT_BUTTON, self.on_N14_range_button)
        self.N15_range_button.Bind(wx.EVT_BUTTON, self.on_N15_range_button)
        self.missed_range_button.Bind(wx.EVT_BUTTON, self.on_missed_range_button)
        self.rtDiff_range_button.Bind(wx.EVT_BUTTON, self.on_rtDiff_range_button)
        self.resid_range_button.Bind(wx.EVT_BUTTON, self.on_resid_range_button)
        if varLab:
            self.FRC_NX_range_button.Bind(wx.EVT_BUTTON, self.on_FRC_NX_range_button)
        
        self.ppmDiffOn.Bind(wx.EVT_CHECKBOX, self.on_ppmDiffOn)
        self.N14On.Bind(wx.EVT_CHECKBOX, self.on_N14On)
        self.N15On.Bind(wx.EVT_CHECKBOX, self.on_N15On)
        self.missedOn.Bind(wx.EVT_CHECKBOX, self.on_missedOn)
        self.rtOn.Bind(wx.EVT_CHECKBOX, self.on_rtOn)
        self.residOn.Bind(wx.EVT_CHECKBOX, self.on_residOn)
        if varLab:
            self.FRC_NXOn.Bind(wx.EVT_CHECKBOX, self.on_FRC_NXOn)

    def on_loadP_button(self, event):
        f = open(self.datapath+'_last.filterParam', 'r')
        params = csv.reader(f)
        pdict = {}
        for l in params:
            pdict[l[0]] = l[1]
        f.close()
        self.lowCheckNum.SetValue(qMS.boolParse(pdict['lowNum']))
        if pulse:
            self.midCheckNum.SetValue(qMS.boolParse(pdict['midNum']))
        self.highCheckNum.SetValue(qMS.boolParse(pdict['highNum']))
        self.lowCheckDen.SetValue(qMS.boolParse(pdict['lowDen']))
        if pulse:
            self.midCheckDen.SetValue(qMS.boolParse(pdict['midDen']))
        self.highCheckDen.SetValue(qMS.boolParse(pdict['highDen']))
        
        self.cb_grid.SetValue(qMS.boolParse(pdict['gridChecked']))
        
        self.ppmDiffRangeBypass.SetValue(pdict['ppmDiff_low'] + ' ' + pdict['ppmDiff_high'])
        self.N14RangeBypass.SetValue(pdict['ppm_n14_low'] + ' ' + pdict['ppm_n14_high'])
        self.N15RangeBypass.SetValue(pdict['ppm_n15_low'] + ' ' + pdict['ppm_n15_high'])
        self.missedRangeBypass.SetValue(pdict['missed_low'] + ' ' + pdict['missed_high'])
        self.rtDiffRangeBypass.SetValue(pdict['rtDiff_low'] + ' ' + pdict['rtDiff_high'])
        if varLab:
            self.FRC_NXRangeBypass.SetValue(pdict['FRC_NX_low'] + ' ' + pdict['FRC_NX_high'])
            self.FRC_NXOn.SetValue(qMS.boolParse(pdict['FRC_NX']))
        self.residRangeBypass.SetValue(pdict['resid_low'] + ' ' + pdict['resid_high'])

        self.ppmDiffOn.SetValue(qMS.boolParse(pdict['ppmDiff']))
        self.N14On.SetValue(qMS.boolParse(pdict['n14']))
        self.N15On.SetValue(qMS.boolParse(pdict['n15']))
        self.missedOn.SetValue(qMS.boolParse(pdict['missed']))
        self.rtOn.SetValue(qMS.boolParse(pdict['rtDiff']))
        self.residOn.SetValue(qMS.boolParse(pdict['resid']))
        
        self.calc_data()     
        
    def on_saveP_button(self, event):
        (ppmDiff_low, ppmDiff_high) = map(str, self.ppmDiffRangeBypass.GetValue().split(' '))
        (ppm_n14_low, ppm_n14_high) = map(str, self.N14RangeBypass.GetValue().split(' '))
        (ppm_n15_low, ppm_n15_high) = map(str, self.N15RangeBypass.GetValue().split(' '))
        (missed_low, missed_high) = map(str, self.missedRangeBypass.GetValue().split(' '))
        (rtDiff_low, rtDiff_high) = map(str, self.rtDiffRangeBypass.GetValue().split(' '))
        if varLab:
            (FRC_NX_low, FRC_NX_high) = map(str, self.FRC_NXRangeBypass.GetValue().split(' '))
        (resid_low, resid_high) = map(str, self.residRangeBypass.GetValue().split(' '))

        outstr = 'param,' + 'value'
        
        outstr = outstr + '\nppmDiff_low,' + ppmDiff_low + '\nppmDiff_high,' + ppmDiff_high
        outstr = outstr + '\nppm_n14_low,' + ppm_n14_low + '\nppm_n14_high,' + ppm_n14_high
        outstr = outstr + '\nppm_n15_low,' + ppm_n15_low + '\nppm_n15_high,' + ppm_n15_high
        outstr = outstr + '\nmissed_low,' + missed_low + '\nmissed_high,' + missed_high
        outstr = outstr + '\nrtDiff_low,' + rtDiff_low + '\nrtDiff_high,' + rtDiff_high
        if varLab:
            outstr = outstr + '\nFRC_NX_low,' + FRC_NX_low + '\nFRC_NX_high,' + FRC_NX_high
            outstr = outstr + '\nFRC_NX,' + str(self.FRC_NXOn.IsChecked())
        outstr = outstr + '\nresid_low,' + resid_low + '\nresid_high,' + resid_high
        
        outstr = outstr + '\ngridChecked,' + str(self.cb_grid.IsChecked())

        outstr = outstr + '\nlowNum,' + str(self.lowCheckNum.IsChecked())
        if pulse:
            outstr = outstr + '\nmidNum,' + str(self.midCheckNum.IsChecked())
        outstr = outstr + '\nhighNum,' + str(self.highCheckNum.IsChecked())
        outstr = outstr + '\nlowDen,' + str(self.lowCheckDen.IsChecked())
        if pulse:
            outstr = outstr + '\nmidDen,' + str(self.midCheckDen.IsChecked())
        outstr = outstr + '\nhighDen,' + str(self.highCheckDen.IsChecked())
        
        outstr = outstr + '\nppmDiff,' + str(self.ppmDiffOn.IsChecked())
        outstr = outstr + '\nn14,' + str(self.N14On.IsChecked())
        outstr = outstr + '\nn15,' + str(self.N15On.IsChecked())
        outstr = outstr + '\nmissed,' + str(self.missedOn.IsChecked())
        outstr = outstr + '\nrtDiff,' + str(self.rtOn.IsChecked())
        outstr = outstr + '\nresid,' + str(self.residOn.IsChecked())

        f = open(self.datapath+'_last.filterParam', 'w')
        f.write(outstr)
        f.close()
    def onr70S_select(self, event):
        self.dataFrame['currentPos'] = self.dataFrame['70Spos']
        self.positionLabels = qMSDefs.positionLabels70S
        self.calc_figure()
        self.draw_left()
    def onr50S_select(self, event):
        self.dataFrame['currentPos'] = self.dataFrame['50Spos']        
        self.positionLabels = qMSDefs.positionLabels50S
        self.calc_figure()
        self.draw_left()
    def onr30S_select(self, event):
        self.dataFrame['currentPos'] = self.dataFrame['30Spos']
        self.positionLabels = qMSDefs.positionLabels30S
        self.calc_figure()
        self.draw_left()

    def on_open_button(self, event):
        """
        Create and show the Open FileDialog
        """
        wildcard =  "Massacre iso_csv file (*_iso.csv)|*_iso.csv|"\
                    "Preprocessed _iso_res.csv file (*_iso_res.csv)|*_iso_res.csv|"\
                    "All files (*.*)|*.*|"
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=self.currentDirectory, 
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        
        if dlg.ShowModal() == wx.ID_OK:
            fullname = dlg.GetPaths()[0].split('/')
            dp = '/'.join(fullname[:-1]) + '/'
            self.currentDirectory = dp
            fn = fullname[-1]
            [df, ci, p, vl] = openFile(dp+fn)
            startApp(df, dp, fn, ci, p, vl)

        dlg.Destroy()
    def on_export_button(self, event):
        """
        Create and show the Save FileDialog
        """
        wildcard =  "Filtered _iso_res_filt.csv file (*_iso_res_filt.csv)|*_iso_res_filt.csv|"\
                    "All files (*.*)|*.*|"
        defFile = self.datafile[:-4]+'_filt.csv'
        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile=defFile, wildcard=wildcard, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            savedPoints = self.getPass(True)
            savedPoints.to_csv(path, index=False)
        dlg.Destroy()
    def on_cb_grid(self, event):
        self.calc_figure()
        self.draw_left()
    def on_ppmDiff_range_button(self, event):
        self.currentHist = "ppmDiff"
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_N14_range_button(self, event):
        self.currentHist = "ppm_n14"
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_N15_range_button(self, event):
        self.currentHist = "ppm_n15"
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_missed_range_button(self, event):
        self.currentHist = "missed"
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_rtDiff_range_button(self, event):
        self.currentHist = "rtDiff"
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_FRC_NX_range_button(self, event):
        self.currentHist = "frac_NX"
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_resid_range_button(self, event):
        self.currentHist = "resid"
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_calc_button(self, event):
        self.calc_data()
        self.calc_figure()
        self.canvasLeft.draw()

    def on_ppmDiffOn(self, event):
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_N14On(self, event):
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_N15On(self, event):
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_missedOn(self, event):
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_rtOn(self, event):
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_residOn(self, event):
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
    def on_FRC_NXOn(self, event):
        self.calc_figure()
        self.calc_hist()
        self.draw_all()

    def on_draw_button(self, event):
        self.calc_figure()
        self.calc_hist()
        self.draw_all()
        
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
        
    def on_exit(self, event):
        self.Destroy()

    def calc_data(self):
        self.UID_output_list = []  
        self.calcNum = self.getChecksNum()
        self.calcDen = self.getChecksDen()
        self.dataFrame['currentCalc'] = qMS.calcValueDF(self.dataFrame, self.calcNum, self.calcDen)
        self.calc_figure()
        self.canvasLeft.draw()
    
    def calc_fit(self):
        plotsfile = self.datapath+self.currentISOFile+'.plots'
        txtfile = self.datapath+self.currentISOFile+'.txt'
        df = pd.read_csv(plotsfile)
        df2 = pd.read_csv(txtfile, header=None, sep=' ')
        del df['residAdj']
#        f = pylab.figure(figsize=(12,10))
#        ax = f.add_subplot(111)
        self.PNGPlot.plot(df2[0][0:len(df['dat'])].values, df['dat'].values, 'ro', markersize=8, label='data', markerfacecolor='None', markeredgecolor='red')
        self.PNGPlot.plot(df2[0][0:len(df['fit'])].values, df['fit'].values, 'b-', linewidth=2, label='fit')
        self.PNGPlot.plot(df2[0][0:len(df['resid'])].values, df['resid'].values, 'g-', linewidth=2, label='residual')
        self.PNGPlot.set_xlabel('m/z')
        self.PNGPlot.set_ylabel('intensity')
        self.PNGPlot.set_xlim(df2[0][0:len(df['dat'])].values.min(), df2[0][0:len(df['dat'])].values.max())
        self.PNGPlot.legend()
        self.PNGPlot.set_title(currentISOFile)
        #img=pylab.imread(getPNG(self.datapath, self.currentISOFile))
        #self.PNGPlot.imshow(img)
        #self.PNGPlot.set_title(self.currentISOFile)
        
            
    def calc_figure(self):
        self.PLPlot.clear()
        self.PLPlot.grid(self.cb_grid.IsChecked())
        savedPoints = self.getPass(True)
        filteredPoints = self.getPass(False)
        self.PLPlot.plot(savedPoints['currentPos'], savedPoints['currentCalc'], 'ro')
        self.PLPlot.plot(filteredPoints['currentPos']+0.25, filteredPoints['currentCalc'], 'bo')
        self.PLPlot.set_xticks(range(1,int(self.dataFrame['currentPos'].max())))
        self.PLPlot.set_xticklabels(self.positionLabels, rotation=90, size='small')
        self.PLPlot.set_title(self.datafile + " : " + setCurrentFrac(self.calcNum, self.calcDen))
        self.PLPlot.set_xlim([0,self.dataFrame['currentPos'].max()])
        self.PLPlot.legend(('Saved', 'Filtered'))

    def calc_hist(self):
        name = self.currentHist
        dataAll = self.dataFrame[self.currentHist]
        dataSelected = self.getPass(True)[name]
        
        bin_num = min(30, len(list(set(dataAll))))
        self.histPlotAll.clear()
        self.histPlotAll.hist(dataAll, bins = bin_num)
        self.histPlotAll.text(0.05,0.75,name+'_All', transform=self.histPlotAll.transAxes)
        
        bin_num = min(80, len(list(set(dataSelected))))
        self.histPlotSelected.clear()
        self.histPlotSelected.hist(dataSelected, bins = bin_num)
        self.histPlotSelected.text(0.05,0.75,name+'_Selected', transform=self.histPlotSelected.transAxes)
    
    def draw_all(self):
        self.canvasLeft.draw()
        self.canvasRight.draw()
    
    def getChecksNum(self):
        toReturn = []        
        if self.lowCheckNum.IsChecked():
            toReturn.append('AMP_U')
        if pulse and self.midCheckNum.IsChecked():
            toReturn.append('AMP_L')
        if self.highCheckNum.IsChecked():
            toReturn.append('AMP_S')
        return toReturn
        
    def getChecksDen(self):
        toReturn = []        
        if self.lowCheckDen.IsChecked():
            toReturn.append('AMP_U')
        if pulse and self.midCheckDen.IsChecked():
            toReturn.append('AMP_L')
        if self.highCheckDen.IsChecked():
            toReturn.append('AMP_S')
        return toReturn
    
    def getPass(self, t):
        (ppmDiff_low, ppmDiff_high) = map(float, self.ppmDiffRangeBypass.GetValue().split(' '))
        (ppm_n14_low, ppm_n14_high) = map(float, self.N14RangeBypass.GetValue().split(' '))
        (ppm_n15_low, ppm_n15_high) = map(float, self.N15RangeBypass.GetValue().split(' '))
        (missed_low, missed_high) = map(float, self.missedRangeBypass.GetValue().split(' '))
        (rtDiff_low, rtDiff_high) = map(float, self.rtDiffRangeBypass.GetValue().split(' '))
        (resid_low, resid_high) = map(float, self.residRangeBypass.GetValue().split(' '))
        usePpm = self.ppmDiffOn.IsChecked()
        useN14 = self.N14On.IsChecked()
        useN15 = self.N15On.IsChecked()
        useMissed = self.missedOn.IsChecked()
        useRTDiff = self.rtOn.IsChecked()
        useResid = self.residOn.IsChecked()
        filt = self.dataFrame['missed'] >=0
        if usePpm:
            filt =  (self.dataFrame['ppmDiff'] >= ppmDiff_low) & (self.dataFrame['ppmDiff'] <= ppmDiff_high) 
        if useN14:
            filt = filt & (self.dataFrame['ppm_n14'] >= ppm_n14_low) & (self.dataFrame['ppm_n14'] <= ppm_n14_high)
        if useN15:
            filt = filt & (self.dataFrame['ppm_n15'] >= ppm_n15_low) & (self.dataFrame['ppm_n15'] <= ppm_n15_high)
        if useMissed:
            filt = filt & (self.dataFrame['missed'] >= missed_low) & (self.dataFrame['missed'] <= missed_high)
        if useRTDiff:
            filt = filt & (self.dataFrame['rtDiff'] >= rtDiff_low) & (self.dataFrame['rtDiff'] <= rtDiff_high)
        if useResid:
            filt = filt & (self.dataFrame['resid'] >= resid_low) & (self.dataFrame['resid'] <= resid_high)
        if varLab:
            (FRC_NX_low, FRC_NX_high) = map(float, self.FRC_NXRangeBypass.GetValue().split(' '))
            useVarlab = self.FRC_NXOn.IsChecked()
            if useVarlab:
                filt = filt & (self.dataFrame['FRC_NX'] >= FRC_NX_low) & (self.dataFrame['FRC_NX'] <= FRC_NX_high)
        if t:
            return self.dataFrame[filt]
        else:
            return self.dataFrame[~filt]
        
def getPNG(datapath, iso):
    return datapath+iso+'.fit.png'

def setCurrentFrac(calcNum, calcDen):
    num = [i[-1:] for i in calcNum]
    den = [i[-1:] for i in calcDen]
    return string.join(num, "+") + " / " + string.join(den, "+")
    
def transformValue(inputData, transformData, toTransform, normalizeTo):
    inputNorm = float(inputData.loc[toTransform])/float(inputData.loc[normalizeTo])
    transformNorm = float(transformData.loc[toTransform])/float(transformData.loc[normalizeTo])
    inputNormOffset = inputNorm - transformNorm
    inputTransformed = inputNormOffset*float(inputData.loc[normalizeTo])
    return inputTransformed

def openFile(fullpath):
    dataFrame = qMS.readIsoCSV(fullpath)
    if not ('resid' in dataFrame.columns):
        dataFrame = qMS.preProcessIsoCSV(fullpath, True)
    
    pulse = 'AMP_L' in dataFrame.columns
    varLab = 'FRC_NX' in dataFrame.columns
    currentISOFile = dataFrame.ix[0]['isofile']
    return [dataFrame, currentISOFile, pulse, varLab]

def startApp(dataFrame, datapath, filename, currentISOFile, pulse, varLab):
    app = wx.App()
    app.frame = MasseFrame(dataFrame, datapath, filename, currentISOFile, pulse=pulse, varLab=varLab)
    app.frame.Show()
    app.MainLoop()    

if __name__ == '__main__':
    datapath = '/home/jhdavis/data/2013_03_11-NCMGradients/SingleSpike/isos/'
    filename = "S21_iso_res.csv"

    [dataFrame, currentISOFile, pulse, varLab] = openFile(datapath+filename)
    startApp(dataFrame, datapath, filename, currentISOFile, pulse, varLab)