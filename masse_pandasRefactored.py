import os
import wx
import qMS
import qMSDefs
import string
import pylab
import csv
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar

class MasseFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'Masse filtering'
    
    def __init__(self, pulse=False, varLab=False):
        wx.Frame.__init__(self, None, -1, self.title)                
        self.create_main_panel(pulse=pulse, varLab=varLab)

        self.calcNum = ["AMP_U"]
        self.calcDen = ["AMP_U", "AMP_S"]
        self.positionLabels = qMSDefs.positionLabels70S
        
        self.lowCheckNum.SetValue(True)
        self.lowCheckDen.SetValue(True)
        self.highCheckDen.SetValue(True)
        self.ppmDiffRangeBypass.SetValue('-100 100')
        self.N14RangeBypass.SetValue('-100 100')
        self.N15RangeBypass.SetValue('-100 100')
        self.missedRangeBypass.SetValue('0 5')        
        self.rtDiffRangeBypass.SetValue('-0.5 0.5')
        self.residRangeBypass.SetValue('0 50')
        if varLab:
            self.FRC_NXRangeBypass.SetValue('0 1')
        
        self.draw_figure()
        self.draw_fit()

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
        
        '''Create the buttons'''
        self.toolbar = NavigationToolbar(self.canvasLeft)
        
        self.cb_grid = wx.CheckBox(self.panel, wx.ID_ANY, label="Show Grid", style=wx.ALIGN_RIGHT)        
        self.drawButton = wx.Button(self.panel, wx.ID_ANY, "Draw!")
        self.exportButton = wx.Button(self.panel, wx.ID_ANY, "Export")
        
        self.r70S = wx.RadioButton(self.panel, label="70S", style=wx.RB_GROUP)
        self.r50S = wx.RadioButton(self.panel, label="50S")
        self.r30S = wx.RadioButton(self.panel, label="30S")
        
        self.savePButton = wx.Button(self.panel, wx.ID_ANY, "Save")
        self.loadPButton = wx.Button(self.panel, wx.ID_ANY, "Load")
        
        self.calcButton = wx.Button(self.panel, wx.ID_ANY, "Calculate")
        
        self.lowCheckNum = wx.CheckBox(self.panel, label="low")
        if pulse:
            self.midCheckNum = wx.CheckBox(self.panel, label="mid")
        self.highCheckNum = wx.CheckBox(self.panel, label="high")
        
        self.lowCheckDen = wx.CheckBox(self.panel, label="low")
        if pulse:
            self.midCheckDen = wx.CheckBox(self.panel, label="mid")
        self.highCheckDen = wx.CheckBox(self.panel, label="high")

        self.ppmDiff_range_button = wx.Button(self.panel, wx.ID_ANY, "PPM difference cutoff")        
        self.N14_range_button = wx.Button(self.panel, wx.ID_ANY, "14N PPM cutoff")        
        self.N15_range_button = wx.Button(self.panel, wx.ID_ANY, "15N PPM cutoff")
        self.missed_range_button = wx.Button(self.panel, wx.ID_ANY, "Missed cleavage cutoff")
        self.rtDiff_range_button = wx.Button(self.panel, wx.ID_ANY, "RT diff cutoff")
        if varLab:
            self.FRC_NX_range_button = wx.Button(self.panel, wx.ID_ANY, "FRC_NX")
        self.resid_range_button = wx.Button(self.panel, wx.ID_ANY, "residual cutoff")
        
        self.ppmDiffRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.N14RangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.N15RangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.missedRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.rtDiffRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        if varLab:
            self.FRC_NXRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.residRangeBypass = wx.TextCtrl(self.panel, size=(100,-1),style=wx.TE_PROCESS_ENTER)

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
        self.imageToolsBox.Add(self.exportButton, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
        self.toolNumBox.Add(self.imageToolsBox, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER)
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
        self.filterBox = wx.StaticBoxSizer(wx.StaticBox(self.panel,wx.ID_ANY,'filters'), wx.HORIZONTAL)
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

        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        
        '''bind events for buttons'''
        self.canvasLeft.mpl_connect('pick_event', self.on_pick)
        self.r70S.Bind(wx.EVT_RADIOBUTTON, self.onr70S_select)
        self.r50S.Bind(wx.EVT_RADIOBUTTON, self.onr50S_select)
        self.r30S.Bind(wx.EVT_RADIOBUTTON, self.onr30S_select)

        self.drawButton.Bind(wx.EVT_BUTTON, self.on_draw_button)
        self.exportButton.Bind(wx.EVT_BUTTON, self.on_export_button)
        self.calcButton.Bind(wx.EVT_BUTTON, self.on_calc_button)
        self.cb_grid.Bind(wx.EVT_CHECKBOX, self.on_cb_grid)
        
        self.loadPButton.Bind(wx.EVT_BUTTON, self.on_loadP_button)
        self.savePButton.Bind(wx.EVT_BUTTON, self.on_saveP_button)

        self.ppmDiff_range_button.Bind(wx.EVT_BUTTON, self.on_ppmDiff_range_button)
        self.N14_range_button.Bind(wx.EVT_BUTTON, self.on_N14_range_button)
        self.N15_range_button.Bind(wx.EVT_BUTTON, self.on_N15_range_button)
        self.missed_range_button.Bind(wx.EVT_BUTTON, self.on_missed_range_button)
        self.rtDiff_range_button.Bind(wx.EVT_BUTTON, self.on_rtDiff_range_button)
        if varLab:
            self.FRC_NX_range_button.Bind(wx.EVT_BUTTON, self.on_FRC_NX_range_button)
        self.resid_range_button.Bind(wx.EVT_BUTTON, self.on_resid_range_button)

    def on_loadP_button(self, event):
        f = open(datapath+'_last.filterParam', 'r')
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
        self.residRangeBypass.SetValue(pdict['resid_low'] + ' ' + pdict['resid_high'])
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

        f = open(datapath+'_last.filterParam', 'w')
        f.write(outstr)
        f.close()
    def onr70S_select(self, event):
        dataFrame['currentPos'] = dataFrame['70Spos']
        self.positionLabels = qMSDefs.positionLabels70S
        self.draw_figure()     
    def onr50S_select(self, event):
        dataFrame['currentPos'] = dataFrame['50Spos']        
        self.positionLabels = qMSDefs.positionLabels50S
        self.draw_figure()     
    def onr30S_select(self, event):
        dataFrame['currentPos'] = dataFrame['30Spos']
        self.positionLabels = qMSDefs.positionLabels30S
        self.draw_figure()

    def on_export_button(self, event):
        print "add export code"
    def on_cb_grid(self, event):
        self.draw_figure()
    def on_ppmDiff_range_button(self, event):
        self.draw_hist("ppmDiff", dataFrame['ppmDiff'], self.getPass(True)['ppmDiff'])
    def on_N14_range_button(self, event):
        self.draw_hist("n14", dataFrame['ppm_n14'], self.getPass(True)['ppm_n14'])
    def on_N15_range_button(self, event):
        self.draw_hist("n15", dataFrame['ppm_n15'], self.getPass(True)['ppm_n15'])
    def on_missed_range_button(self, event):
        self.draw_hist("missed", dataFrame['missed'], self.getPass(True)['missed'])
    def on_rtDiff_range_button(self, event):
        self.draw_hist("rtDiff", dataFrame['rtDiff'], self.getPass(True)['rtDiff'])
    def on_FRC_NX_range_button(self, event):
        self.draw_hist("frac_NX", dataFrame['FRC_NX'], self.getPass(True)['FRC_NX'])
    def on_resid_range_button(self, event):
        self.draw_hist("resid", dataFrame['resid'], self.getPass(True)['resid'])
        #calcResidual()
    def on_calc_button(self, event):
        self.calc_data()
    def on_draw_button(self, event):
        self.draw_figure()
        
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
            self.canvasLeft.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
            
    def on_exit(self, event):
        self.Destroy()
    
    def draw_fit(self):
        img=pylab.imread(getPNG(datapath, currentISOFile))
        self.PNGPlot.imshow(img)
        self.PNGPlot.set_title(currentISOFile)
        self.canvasRight.draw()

    def calc_data(self):
        self.UID_output_list = []  
        self.calcNum = self.getChecksNum()
        self.calcDen = self.getChecksDen()
        dataFrame['currentCalc'] = qMS.calcValueDF(dataFrame, self.calcNum, self.calcDen)
        self.draw_figure()
            
    def draw_figure(self):
        self.PLPlot.clear()
        self.PLPlot.grid(self.cb_grid.IsChecked())
        self.PLPlot.plot(self.getPass(True)['currentPos'], self.getPass(True)['currentCalc'], 'ro')
        self.PLPlot.plot(self.getPass(False)['currentPos']+0.25, self.getPass(False)['currentCalc'], 'bo')
        self.PLPlot.set_xticks(range(1,int(dataFrame['currentPos'].max())))
        self.PLPlot.set_xticklabels(self.positionLabels, rotation=90, size='small')
        self.PLPlot.set_title(datafile + " : " + setCurrentFrac(self.calcNum, self.calcDen))
        self.PLPlot.set_xlim([0,dataFrame['currentPos'].max()])
        self.canvasLeft.draw()

    def draw_hist(self, name, dataAll, dataSelected):
        bin_num = min(30, len(list(set(dataAll))))
        self.histPlotAll.clear()
        self.histPlotAll.hist(dataAll, bins = bin_num)
        self.histPlotAll.text(0.05,0.75,name+'_All', transform=self.histPlotAll.transAxes)
        bin_num = min(80, len(list(set(dataSelected))))
        self.histPlotSelected.clear()
        self.histPlotSelected.hist(dataSelected, bins = bin_num)
        self.histPlotSelected.text(0.05,0.75,name+'_Selected', transform=self.histPlotSelected.transAxes)
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
        if varLab:
            (FRC_NX_low, FRC_NX_high) = map(float, self.FRC_NXRangeBypass.GetValue().split(' '))
        (resid_low, resid_high) = map(float, self.residRangeBypass.GetValue().split(' '))
        filt =  (dataFrame['ppmDiff'] >= ppmDiff_low) & (dataFrame['ppmDiff'] <= ppmDiff_high) & \
                (dataFrame['ppm_n14'] >= ppm_n14_low) & (dataFrame['ppm_n14'] <= ppm_n14_high) & \
                (dataFrame['ppm_n15'] >= ppm_n15_low) & (dataFrame['ppm_n15'] <= ppm_n15_high) & \
                (dataFrame['missed'] >= missed_low) & (dataFrame['missed'] <= missed_high) & \
                (dataFrame['rtDiff'] >= rtDiff_low) & (dataFrame['rtDiff'] <= rtDiff_high) & \
                (dataFrame['resid'] >= resid_low) & (dataFrame['resid'] <= resid_high)
        if varLab:
            filt = filt & (dataFrame['FRC_NX'] >= FRC_NX_low) & (dataFrame['FRC_NX'] <= FRC_NX_high)
        if t:
            return dataFrame[filt]
        else:
            return dataFrame[~filt]
        
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

if __name__ == '__main__':
    datapath = '/home/jhdavis/data/2013_03_11-NCMGradients/SingleSpike/S20/'
    pulse=True
    varLab=False
    #datafile = "S20_iso.csv"
    #qMS.preProcessIsoCSV(datapath+datafile, pulse, False)
    datafile = "S20_iso_res.csv"
    dataFrame = qMS.readIsoCSV(datapath+datafile, pulse=pulse, varLab=varLab)
    currentISOFile = dataFrame.ix[0]['isofile']
    app = wx.App()
    app.frame = MasseFrame(pulse, varLab)
    app.frame.Show()
    app.MainLoop()
    
