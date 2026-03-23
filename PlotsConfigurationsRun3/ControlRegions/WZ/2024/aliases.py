import os
import copy
import inspect

# /afs/cern.ch/user/n/ntrevisa/work/latinos/Run3/PlotsConfigurationsRun3/ControlRegions/WZ/2022_v12
configurations = os.path.realpath(inspect.getfile(inspect.currentframe())) # this file
configurations = os.path.dirname(configurations) # 2022_v12
configurations = os.path.dirname(configurations) # WZ
configurations = os.path.dirname(configurations) # ControlRegions
configurations = os.path.dirname(configurations) # PlotsConfigurationsRun3

aliases = {}
aliases = OrderedDict()

mc     = [skey for skey in samples if skey not in ('Fake', 'DATA', 'Dyemb', 'DATA_EG', 'DATA_Mu', 'DATA_EMu', 'Fake_EG', 'Fake_Mu', 'Fake_EMu')]
mc_emb = [skey for skey in samples if skey not in ('Fake', 'DATA', 'DATA_Mu', 'DATA_EMu', 'Fake_EG', 'Fake_Mu', 'Fake_EMu')]

# LepCut3l__ele_mvaWinter22V2Iso_WP90__mu_cut_TightID_POG
eleWP = 'cutBased_LooseID_tthMVA_Run3'
muWP  = 'cut_TightID_pfIsoTight_HWW_tthmva_67'

aliases['LepWPCut'] = {
    'expr': 'LepCut3l__ele_'+eleWP+'__mu_'+muWP,
    'samples': mc + ['DATA'],
}

aliases['LepWPSF'] = {
    'expr': 'LepSF3l__ele_'+eleWP+'__mu_'+muWP,
    'samples': mc
}

# gen-matching to prompt only (GenLepMatch3l matches to *any* gen lepton)
aliases['PromptGenLepMatch3l'] = {
    'expr': 'Alt(Lepton_promptgenmatched, 0, 0) * Alt(Lepton_promptgenmatched, 1, 0) * Alt(Lepton_promptgenmatched, 2, 0)',
    'samples': mc
}

# Conept
aliases['Lepton_conept'] = {
    'linesToAdd': [
        '#include "/afs/cern.ch/user/s/sballav/private/VH/PlotsConfigurationsRun3/utils/macros/LeptonConePt_class.cc"'
    ],
    'expr': 'LeptonConePt(Lepton_pt, Lepton_pdgId, Lepton_electronIdx, Lepton_muonIdx, Electron_jetRelIso, Muon_jetRelIso)',
    'samples': mc + ['Fake', 'DATA']
}


# Fake leptons transfer factor
aliases['fakeW'] = {
    'linesToAdd': [
        '#include "/afs/cern.ch/user/s/sballav/private/VH/PlotsConfigurationsRun3/utils/macros/fake_rate_reader_class_run3.cc"'
    ],
    'linesToProcess': [
        f'''ROOT.gInterpreter.Declare(
            'fake_rate_reader fr_reader("{eleWP}", "{muWP}", "nominal", 3, "std", "/afs/cern.ch/user/s/sballav/private/VH/PlotsConfigurationsRun3/utils/data/FakeRate/2024_v15_conept");'
        )'''
    ],
    'expr': f'fr_reader(Lepton_pdgId, Lepton_conept, Lepton_eta, Lepton_isTightMuon_{muWP}, Lepton_isTightElectron_{eleWP}, Lepton_muonIdx, CleanJet_pt, nCleanJet)',
    'samples': ['Fake']
}


# Jet bins
# using Alt(CleanJet_pt, n, 0) instead of Sum(CleanJet_pt >= 30) because jet pt ordering is not strictly followed in JES-varied samples

# No jet with pt > 30 GeV
aliases['zeroJet'] = {
    'expr': 'Alt(CleanJet_pt, 0, 0) < 30.'
}

aliases['oneJet'] = {
    'expr': 'Alt(CleanJet_pt, 0, 0) > 30.'
}

aliases['multiJet'] = {
    'expr': 'Alt(CleanJet_pt, 1, 0) > 30.'
}

aliases['noJetInHorn'] = {
    'expr' : 'Sum(CleanJet_pt > 30 && CleanJet_pt < 50 && abs(CleanJet_eta) > 2.6 && abs(CleanJet_eta) < 3.1) == 0',
}

########################################################################
# B-Tagging WP: https://btv-wiki.docs.cern.ch/ScaleFactors/Run3Summer22/
########################################################################

# Algo / WP / WP cut
btagging_WPs = {
    "UParTAK4B" : {
        "loose"    : "0.0246",
        "medium"   : "0.1272",
        "tight"    : "0.4648",
        "xtight"   : "0.6298",
        "xxtight"  : "0.9739",
    }
}

# Algo / SF name
btagging_SFs = {
    "UParTAK4B"      : "upart",
}

# Algorithm and WP selection
bAlgo = 'UParTAK4B' # ['DeepFlavB','RobustParTAK4B','PNetB'] 
WP    = 'loose'     # ['loose','medium','tight','xtight','xxtight']

# Access information from dictionaries
bWP   = btagging_WPs[bAlgo][WP]
bSF   = btagging_SFs[bAlgo]

# B tagging selections and scale factors
aliases['bVeto'] = {
    'expr': f'Sum(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5 && Take(Jet_btag{bAlgo}, CleanJet_jetIdx) > {bWP}) == 0'
}

# aliases['bVetoSF'] = {
#     'expr': 'TMath::Exp(Sum(LogVec((CleanJet_pt>20 && abs(CleanJet_eta)<2.5)*Take(Jet_btagSF_{}_shape, CleanJet_jetIdx)+1*(CleanJet_pt<20 || abs(CleanJet_eta)>2.5))))'.format(bSF),
#     'samples': mc
# }

aliases['bReq'] = { 
    'expr': f'Sum(CleanJet_pt > 30. && abs(CleanJet_eta) < 2.5 && Take(Jet_btag{bAlgo}, CleanJet_jetIdx) > {bWP}) >= 1'
}

# aliases['bReqSF'] = {
#     'expr': 'TMath::Exp(Sum(LogVec((CleanJet_pt>30 && abs(CleanJet_eta)<2.5)*Take(Jet_btagSF_{}_shape, CleanJet_jetIdx)+1*(CleanJet_pt<30 || abs(CleanJet_eta)>2.5))))'.format(bSF),
#     'samples': mc
# }

# Top control region
aliases['topcr'] = {
    'expr': 'mtw2>30 && mll>50 && ((zeroJet && !bVeto) || bReq)'
}

# WW control region
aliases['wwcr'] = {
    'expr': 'mth>60 && mtw2>30 && mll>100 && bVeto'
}

# Overall b tag SF
#aliases['btagSF'] = {
#    'expr': '(bVeto || (topcr && zeroJet))*bVetoSF + (topcr && !zeroJet)*bReqSF',
#    'samples': mc
#}
'''
eff_map_year = '2024' # ['2022', '2022EE', '2023BPix', '2023BPixBPix']
year = 'Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15' # ['Run3-22CDSep23-Summer22-NanoAODv12', 'Run3-22EFGSep23-Summer22EE-NanoAODv12, 'Run3-23CSep23-Summer23-NanoAODv12', 'Run3-23DSep23-Summer23BPix-NanoAODv12', 'Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15']

shifts_per_flavour = {
    'bc': ['central', 'down', 'down_fsrdef', 'down_hdamp', 'down_isrdef', 'down_jer', 'down_jes', 'down_mass', 'down_statistic', 'down_tune', 'up', 'up_fsrdef', 'up_hdamp', 'up_isrdef', 'up_jer', 'up_jes', 'up_mass', 'up_statistic', 'up_tune'],
    'light': ['central', 'down', 'down_correlated', 'down_uncorrelated', 'up', 'up_correlated', 'up_uncorrelated'],
}

for flavour in ['bc', 'light']:
    for shift in shifts_per_flavour[flavour]:
        btagsf = 'btagSF' + flavour
        if shift != 'central':
            btagsf += '_' + shift
        aliases[btagsf] = {
            'linesToAdd': [f'#include "{configurations}extended/evaluate_btagSF{flavour}.cc"'],
            'linesToProcess': [f"ROOT.gInterpreter.Declare('btagSF{flavour} btagSF{flavour}_{shift} = btagSF{flavour}(\"/afs/cern.ch/user/s/sballav/private/VH/PlotsRun3_2023/ControlRegions/WZ/data/btag_eff/bTagEff_{2024}_ttbar_{loose}.root\", \"{year}\");')"],
            'expr': f'btagSF{flavour}_{shift}(CleanJet_pt, CleanJet_eta, CleanJet_jetIdx, nCleanJet, Jet_hadronFlavour, Jet_btag{bAlgo}, "{WP_eval}", "{shift}", "{tagger}","{eff_map_year}")',
            'samples' : mc,
        }
'''

# # Systematic uncertainty variations
# for shift in ['jes','lf','hf','lfstats1','lfstats2','hfstats1','hfstats2','cferr1','cferr2']:

#     for targ in ['bVeto', 'bReq']:
#         alias = aliases['%sSF%sup' % (targ, shift)] = copy.deepcopy(aliases['%sSF' % targ])
#         alias['expr'] = alias['expr'].replace('btagSF_deepjet_shape', 'btagSF_deepjet_shape_up_%s' % shift)

#         alias = aliases['%sSF%sdown' % (targ, shift)] = copy.deepcopy(aliases['%sSF' % targ])
#         alias['expr'] = alias['expr'].replace('btagSF_deepjet_shape', 'btagSF_deepjet_shape_down_%s' % shift)

#     aliases['btagSF%sup' % shift] = {
#         'expr': aliases['btagSF']['expr'].replace('SF', 'SF' + shift + 'up'),
#         'samples': mc
#     }

#     aliases['btagSF%sdown' % shift] = {
#         'expr': aliases['btagSF']['expr'].replace('SF', 'SF' + shift + 'down'),
#         'samples': mc
#     }

##########################################################################
# End of b tagging
##########################################################################

# Data/MC scale factors and systematic uncertainties
aliases['SFweight'] = {
    #'expr': ' * '.join(['SFweight3l', 'LepWPCut', 'LepWPSF', 'btagSFbc', ' btagSFlight']),
    'expr': ' * '.join(['SFweight3l', 'LepWPCut', 'LepWPSF']),
    'samples': mc
}

aliases['SFweightEleUp'] = {
    'expr': 'LepSF3l__ele_'+eleWP+'__Up',
    'samples': mc
}
aliases['SFweightEleDown'] = {
    'expr': 'LepSF3l__ele_'+eleWP+'__Down',
    'samples': mc
}
aliases['SFweightMuUp'] = {
    'expr': 'LepSF3l__mu_'+muWP+'__Up',
    'samples': mc
}
aliases['SFweightMuDown'] = {
    'expr': 'LepSF3l__mu_'+muWP+'__Down',
    'samples': mc
}

# # WH3l_mOSll for data
# aliases['WH3l_mOSll'] = {
#     'linesToAdd' : [f'#include "{configurations}/ControlRegions/WZ/macros/mOS_ll.cc"'],
#     'class'      : 'mOS_ll',
#     'args'       : 'nLepton,Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId',
#     'samples'    : ['DATA'],
# }

# # WH3l_mlll for data
# aliases['WH3l_mlll'] = {
#     'linesToAdd' : [f'#include "{configurations}/ControlRegions/WZ/macros/m_lll.cc"'],
#     'class'      : 'm_lll',
#     'args'       : 'nLepton,Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId',
#     'samples'    : ['DATA'],
# }

# # WH3l_ZVeto for data
# aliases['WH3l_ZVeto'] = {
#     'linesToAdd' : [f'#include "{configurations}/ControlRegions/WZ/macros/z_veto.cc"'],
#     'class'      : 'z_veto',
#     'args'       : 'nLepton,Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId',
#     'samples'    : ['DATA'],
# }

# # WH3l_flagOSSF for data
# aliases['WH3l_flagOSSF'] = {
#     'linesToAdd' : [f'#include "{configurations}/ControlRegions/WZ/macros/flag_ossf.cc"'],
#     'class'      : 'flag_ossf',
#     'args'       : 'nLepton,Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId',
#     'samples'    : ['DATA'],
# }

# # WH3l_flagOSSF for data
# aliases['WH3l_chlll'] = {
#     'linesToAdd' : [f'#include "{configurations}/ControlRegions/WZ/macros/ch_lll.cc"'],
#     'class'      : 'ch_lll',
#     'args'       : 'nLepton,Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId',
#     'samples'    : ['DATA'],
# }
