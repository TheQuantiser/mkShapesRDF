from mkShapesRDF.lib.search_files import SearchFiles

searchFiles = SearchFiles()

redirector = ""
useXROOTD = False

# MC:   /eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer22_130x_nAODv12_Full2022v12/MCl2loose2022v12__MCCorr2022v12JetScaling__l2tight
# DATA: /eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Run2022_ReReco_nAODv12_Full2022v12/DATAl2loose2022v12__l2tight

mcProduction = 'Summer24_150x_nAODv15_Full2024v15'
mcSteps      = 'MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight'
dataRecoMuon     = 'Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15_Muon'
dataRecoEGamma     = 'Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15_EGamma'
dataRecoMuonEG     = 'Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15_MuonEG'
dataSteps    = 'DATAl2loose2024v15__l2loose'

##############################################
###### Tree base directory for the site ######
##############################################/
treeBaseDir = '/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/'
limitFiles = -1

def makeMCDirectory(var=""):
    _treeBaseDir = treeBaseDir + ""
    if redirector != "":
        _treeBaseDir = redirector + treeBaseDir
    if var == "":
        return "/".join([_treeBaseDir, mcProduction, mcSteps])
    else:
        return "/".join([_treeBaseDir, mcProduction, mcSteps + "__" + var])


mcDirectory   = makeMCDirectory()
fakeDirectoryMuon = os.path.join(treeBaseDir, dataRecoMuon, dataSteps)
dataDirectoryMuon = os.path.join(treeBaseDir, dataRecoMuon, dataSteps)
fakeDirectoryEGamma = os.path.join(treeBaseDir, dataRecoEGamma, dataSteps)
dataDirectoryEGamma = os.path.join(treeBaseDir, dataRecoEGamma, dataSteps)
fakeDirectoryMuonEG = os.path.join(treeBaseDir, dataRecoMuonEG, dataSteps)
dataDirectoryMuonEG = os.path.join(treeBaseDir, dataRecoMuonEG, dataSteps)

samples = {}


def nanoGetSampleFiles(path, name):
    _files = searchFiles.searchFiles(path, name, redirector=redirector)
    if limitFiles != -1 and len(_files) > limitFiles:
        return [(name, _files[:limitFiles])]
    else:
        return [(name, _files)]


def CombineBaseW(samples, proc, samplelist):
    _filtFiles = list(filter(lambda k: k[0] in samplelist, samples[proc]["name"]))
    _files = list(map(lambda k: k[1], _filtFiles))
    _l = list(map(lambda k: len(k), _files))
    leastFiles = _files[_l.index(min(_l))]
    dfSmall = ROOT.RDataFrame("Runs", leastFiles)
    s = dfSmall.Sum("genEventSumw").GetValue()
    f = ROOT.TFile(leastFiles[0])
    t = f.Get("Events")
    t.GetEntry(1)
    xs = t.baseW * s

    __files = []
    for f in _files:
        __files += f
    df = ROOT.RDataFrame("Runs", __files)
    s = df.Sum("genEventSumw").GetValue()
    newbaseW = str(xs / s)
    weight = newbaseW + "/baseW"

    for iSample in samplelist:
        addSampleWeight(samples, proc, iSample, weight)


def addSampleWeight(samples, sampleName, sampleNameType, weight):
    obj = list(filter(lambda k: k[0] == sampleNameType, samples[sampleName]["name"]))[0]
    samples[sampleName]["name"] = list(
        filter(lambda k: k[0] != sampleNameType, samples[sampleName]["name"])
    )
    if len(obj) > 2:
        samples[sampleName]["name"].append(
            (obj[0], obj[1], obj[2] + "*(" + weight + ")")
        )
    else:
        samples[sampleName]["name"].append((obj[0], obj[1], "(" + weight + ")"))


################################################
############ DATA DECLARATION ##################
################################################

DataRun = [
    ['C','Run2024C-ReReco-v1'],
    ['D','Run2024D-ReReco-v1'],
    ['E','Run2024E-ReReco-v1'],
    ['F','Run2024F-Prompt-v1'],
    ['G','Run2024G-Prompt-v1'],
    ['H','Run2024H-Prompt-v1'],
    ['I','Run2024I-Prompt-v1'],
]

DataSets = ['MuonEG','Muon0','Muon1','EGamma0','EGamma1']

DataTrig = {
    'MuonEG'         : ' Trigger_ElMu' ,
    'Muon0'           : '!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)',
    'Muon1'           : '!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)',
    'EGamma0'         : '!Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu && (Trigger_sngEl || Trigger_dblEl)',
    'EGamma1'         : '!Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu && (Trigger_sngEl || Trigger_dblEl)',
}

#########################################
############ MC COMMON ##################
#########################################

# SFweight does not include btag weights
mcCommonWeightNoMatch = 'XSWeight*METFilter_Common*SFweight'
mcCommonWeight        = 'XSWeight*METFilter_Common*PromptGenLepMatch3l*SFweight'

#mcCommonWeight = 'XSWeight*METFilter_Common*SFweight'

###########################################
#############  BACKGROUNDS  ###############
###########################################

# ZZ
files = nanoGetSampleFiles(mcDirectory, 'ZZ')

samples['ZZ'] = {
    'name': files,
    'weight': mcCommonWeight,
    'FilesPerJob': 50,
}

# VVV
files = nanoGetSampleFiles(mcDirectory, 'WWW')+ \
        nanoGetSampleFiles(mcDirectory, 'WWZ')+ \
        nanoGetSampleFiles(mcDirectory, 'WZZ')+ \
        nanoGetSampleFiles(mcDirectory, 'ZZZ')


samples['VVV'] = {
    'name': files,
    'weight': mcCommonWeight,
    'FilesPerJob': 50,
}

#ttW
files = nanoGetSampleFiles(mcDirectory, 'TTLNu')

samples['ttW'] = {
    'name': files,
    'weight': mcCommonWeight,
    'FilesPerJob': 50,
}

#DYG
files = nanoGetSampleFiles(mcDirectory, 'DYGto2LG-1Jets_Bin-MLL-50')+ \
        nanoGetSampleFiles(mcDirectory, 'DYGto2LG-1Jets_Bin-MLL-4to50')

samples['DYG'] = {
    'name': files,
    'weight': mcCommonWeight,
    'FilesPerJob': 50,
}

# WZ
files = nanoGetSampleFiles(mcDirectory, 'WZTo3LNu')

samples['WZ'] = {
    'name': files,
    'weight': mcCommonWeight,
    'FilesPerJob': 50,
}

###########################################
################## DATA ###################
###########################################

samples['DATA'] = { 
    'name': [],  
    'weight': 'LepWPCut*METFilter_DATA',     
    'weights': [], 
    'isData': ['all'], 
    'FilesPerJob': 100 
} 

for _, sd in DataRun:
  for pd in DataSets:
    datatag = pd + '_' + sd

    if datatag.startswith('MuonEG'):
        files = nanoGetSampleFiles(dataDirectoryMuonEG, datatag)
    elif datatag.startswith('Muon'):
        files = nanoGetSampleFiles(dataDirectoryMuon, datatag)
    elif datatag.startswith('EGamma'):
        files = nanoGetSampleFiles(dataDirectoryEGamma, datatag)
    
    print(datatag)

    samples['DATA']['name'].extend(files)
    addSampleWeight(samples, 'DATA', datatag, DataTrig[pd])

###########################################
################## FAKE ###################
###########################################

samples['Fake'] = {
    'name': [],
    'weight': 'METFilter_DATA*fakeW',
    'weights': [],
    'isData': ['all'],
    'FilesPerJob': 100
}


for _, sd in DataRun:
  for pd in DataSets:
    datatag = pd + '_' + sd

    if datatag.startswith('MuonEG'):
        files = nanoGetSampleFiles(fakeDirectoryMuonEG, datatag)
    elif datatag.startswith('Muon'):
        files = nanoGetSampleFiles(fakeDirectoryMuon, datatag)
    elif datatag.startswith('EGamma'):
        files = nanoGetSampleFiles(fakeDirectoryEGamma, datatag)

    samples['Fake']['name'].extend(files)
    addSampleWeight(samples, 'Fake', datatag, DataTrig[pd])