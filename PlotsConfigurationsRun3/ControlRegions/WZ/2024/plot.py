# Group of plots

groupPlot = {}

groupPlot['ZZ'] = {
    'nameHR'   : 'ZZ',
    'isSignal' : 0,
    'color'    : 418, # kGreen + 2
    'samples'  : ['ZZ']
}

groupPlot['VVV']  = {  
    'nameHR'   : 'VVV',
    'isSignal' : 0,
    'color'    : 400, # kYellow
    'samples'  : ['VVV']
}

groupPlot['ttW'] = {
    'nameHR'   : 'ttW',
    'isSignal' : 0,
    'color'    : 425, # kCyan - 7
    'samples'  : ['ttW']
}

groupPlot['DYG']  = {  
    'nameHR'   : 'DYG',
    'isSignal' : 0,
    'color'    : 797, # kOrange - 3
    'samples'  : ['DYG']
}

groupPlot['WZ']  = {  
    'nameHR'   : 'WZ',
    'isSignal' : 0,
    'color'    : 619, # kViolet + 1
    'samples'  : ['WZ']
}

groupPlot['Fake']  = {
    'nameHR' : 'nonprompt',
    'isSignal' : 0,
    'color': '#94a4a2',    # 921 kGray + 1                                                                                                                          
    'samples'  : ['Fake']
}

# Plots

plot = {}

plot['ZZ']  = {  
    'nameHR'   : 'ZZ',
    'color'    : 418, # kGreen + 2
    'isSignal' : 0,
    'isData'   : 0, 
    'scale'    : 1.0,
}

plot['VVV']  = {  
    'nameHR'   : 'VVV',
    'color'    : 400, # kKYellow
    'isSignal' : 0,
    'isData'   : 0, 
    'scale'    : 1.0,
}

plot['ttW']  = {  
    'nameHR'   : 'ttW',
    'color'    : 425, # kCyan - 7
    'isSignal' : 0,
    'isData'   : 0, 
    'scale'    : 1.0,
}

plot['DYG']  = {  
    'nameHR'   : 'DYG',
    'color'    : 797, # kOrange - 3
    'isSignal' : 0,
    'isData'   : 0, 
    'scale'    : 1.0,
}

plot['WZ']  = {  
    'nameHR'   : 'WZ',
    'color'    : 619, # kKYellow
    'isSignal' : 0,
    'isData'   : 0, 
    'scale'    : 1.0,
}

plot['Fake']  = {
    'nameHR'   : 'nonprompt',
    'color'    : 921,
    'isSignal' : 0,
    'isData'   : 0,
    'scale'    : 1.0,
}

# Data

plot['DATA']  = { 
    'nameHR'   : 'Data',
    'color'    : 1 ,  
    'isSignal' : 0,
    'isData'   : 1 ,
    'isBlind'  : 0
}


# Legend definition
legend = {}
legend['lumi'] = 'L = 109.08 fb^{-1}'
legend['sqrt'] = '#sqrt{s} = 13.6 TeV'
