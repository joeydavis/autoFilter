# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 16:30:13 2015

@author: jhdavis
"""

import pandas
import qMS
import numpy
import scipy
import sys


def readFileListing(fileListString):
    fileList = [i.rstrip() for i in open(fileListString).readlines()]
    return fileList

def readSingleIsoCSV(path, shortName=None):
    dataset = qMS.readIsoCSV(path)
    if shortName is None:
        shortName = path
    dataset['originFile'] = shortName

    s = '_'
    dataset['UID'] =  dataset['originFile'] +s+ dataset['protein'] +s+ dataset['startres'].map(str).str.split('.').str[0] +s+\
                        dataset['endres'].map(str).str.split('.').str[0] +s+ dataset['mw'].map(str).str.split('.').str[0] +s+ \
                        dataset['charge'].map(str).str.split('.').str[0] +s+ dataset['rt_n14'].map(str).str.split('.').str[0]
    dataset['TID'] =  dataset['protein'] +s+ dataset['startres'].map(str).str.split('.').str[0] +s+\
                        dataset['endres'].map(str).str.split('.').str[0] +s+ dataset['mw'].map(str).str.split('.').str[0] +s+ \
                        dataset['charge'].map(str).str.split('.').str[0]
    return dataset

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fileListString=sys.argv[1]
    else:
        fileListString='/home/jhdavis/data/emDeps/emrSet/testFileList.txt'

    if len(sys.argv) > 2:
        outputFileString=sys.argv[2]
    else:
        outputFileString='/home/jhdavis/data/emDeps/emrSet/testOutput_mergedCSV.csv'
        
    fileList = readFileListing(fileListString)
    
    fullDataset = pandas.DataFrame()
    for f in fileList:
        sn = f.split('/')[-1].split('_')[0]
        fullDataset = fullDataset.append(readSingleIsoCSV(f, shortName=sn), ignore_index=True)
    fullDataset.to_csv(outputFileString, index=False)