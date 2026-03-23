cuts = {}

# Preselections - applied to all the cuts
preselections = 'Alt(Lepton_pt,0,0)>25 \
              && Alt(Lepton_pt,1,0)>20 \
              && Alt(Lepton_pt,2,0)>15 \
              && (nLepton>=3 && Alt(Lepton_pt,3,0)<1) \
              && (WH3l_mOSll[0] < 0 || WH3l_mOSll[0] > 12) \
              && (WH3l_mOSll[1] < 0 || WH3l_mOSll[1] > 12) \
              && (WH3l_mOSll[2] < 0 || WH3l_mOSll[2] > 12) \
              && abs(WH3l_chlll) == 1 \
              && bVeto \
              && noJetInHorn \
'



# Inclusive 
cuts['wh3l_wz_13TeV'] = (
    'WH3l_flagOSSF == 1 && '
    'PuppiMET_pt > 45 && '
    'WH3l_ZVeto < 20 && '
    'WH3l_mlll > 100 && '
    'Alt(CleanJet_pt,0,0) < 30 && '
    'Sum(CleanJet_pt > 20. && abs(CleanJet_eta) < 2.5) == 0'
)

'''
cuts['Zee']  = {
   'expr' : '(Lepton_pdgId[0] * Lepton_pdgId[1] == -11*11) && abs(WH3l_mOSll[0] - 91.2) < 15',
   'categories' : {
       'Inc' : '1',
  }
}

cuts['Zmm']  = {
    'expr' : '(Lepton_pdgId[0] * Lepton_pdgId[1] == -13*13) && abs(WH3l_mOSll[0] - 91.2) < 15',
    'categories' : {
        'Inc' : '1',
    }
}
'''

cuts['Zee'] = (
    cuts['wh3l_wz_13TeV'] +
    ' && abs(WH3l_mOSll[0] - 91.2) < 15'
    ' && ('
    ' (Lepton_pdgId[0]*Lepton_pdgId[1] == -11*11) ||'
    ' (Lepton_pdgId[0]*Lepton_pdgId[2] == -11*11) ||'
    ' (Lepton_pdgId[1]*Lepton_pdgId[2] == -11*11)'
    ' )'
)



cuts['Zmm'] = (
    cuts['wh3l_wz_13TeV'] +
    ' && abs(WH3l_mOSll[0] - 91.2) < 15'
    ' && ('
    ' (Lepton_pdgId[0]*Lepton_pdgId[1] == -13*13) ||'
    ' (Lepton_pdgId[0]*Lepton_pdgId[2] == -13*13) ||'
    ' (Lepton_pdgId[1]*Lepton_pdgId[2] == -13*13)'
    ' )'
)