import ROOT
import os, sys
import argparse
import numpy as np
from array import array
import json

# Define lepton type
lepton = sys.argv[1] 

# Data
data = sys.argv[2] 

# Eta option: Eta or noEta
etaOption = sys.argv[3]

# Data era
era = sys.argv[4]

# Output histograms file
outputHistos = sys.argv[5]

# Input ROOT files
inputFiles = sys.argv[6:]

lep1pt_bin_edges = array('d', [
    0, 2, 4, 6, 8, 10, 12,
    14, 16, 18, 20, 22,
    24, 26, 28, 30, 32,
    34, 36, 38, 40, 50,
    60, 70, 80, 90, 100,
    120, 140, 160, 180, 200
])


refhlt = "HLT_PFMETNoMu120_PFMHTNoMu120_IDTight"

# Initialize total number of events and cross-section
total_events = 0
cross_section = 0

# Set luminosity based on era
luminosities = {
    "2016APV": 19520,
    "2016": 16810,
    "2017": 41480,
    "2018": 59830
}

# Get the luminosity for the specified era
luminosity = luminosities.get(era, None)
if luminosity is None:
    raise ValueError(f"Luminosity for era '{era}' is not defined.")

# Lepton-specific configurations
if lepton == "Muon":
    hlt = ["HLT_IsoMu27", "HLT_Mu50"]
    if data == "data":
        offlineCuts = {
            "lep1pt": 40,
            "MET": 200,
            "mT": (30, 130),
            "Boson pT": 200
        }
    
    else:
        offlineCuts = {
            "lep1pt": 40,
            "MET": 30,
            "mT": (30, 130),
            "Boson pT": 200
        }

    histBins = {
        "lep1pt": lep1pt_bin_edges,
        "MET": [30, 0, 300],
        "mT": [15, 0, 150],
        "lep1phi": [35, 0, 3.5],
        "MET phi": [35, 0, 3.5],
        "Boson pT": [80, 0, 800]
    }

    pt_label = "Muon pT [GeV]"
    eta_bins = ["eta1", "eta2", "eta3"]
    eta_ranges = [(0.0, 0.9), (0.9, 2.1), (2.1, 2.4)]
else:
    if era == "2018":
        hlt = ["HLT_Ele32_WPTight_Gsf", "HLT_Ele115_CaloIdVT_GsfTrkIdT"]
    elif era == "2017":
        hlt = ["HLT_Ele35_WPTight_Gsf", "HLT_Ele115_CaloIdVT_GsfTrkIdT"]
    elif era in ["2016", "2016APV"]:
        hlt = ["HLT_Ele27_WPTight_Gsf", "HLT_Ele115_CaloIdVT_GsfTrkIdT", "HLT_Photon175"]

    if data == "data":
        offlineCuts = {
            "lep1pt": 30,
            "MET": 200,
            "mT": (30, 130),
            "Boson pT": 200
        }
    
    else:
        offlineCuts = {
            "lep1pt": 30,
            "MET": 30,
            "mT": (30, 130),
            "Boson pT": 200
        }

    histBins = {
        "lep1pt": lep1pt_bin_edges,
        "MET": [30, 0, 300],
        "mT": [15, 0, 150],
        "lep1phi": [35, 0, 3.5],
        "MET phi": [35, 0, 3.5],
        "Boson pT": [40, 0, 400]
    }

    pt_label = "Electron pT [GeV]"
    eta_bins = ["eta1", "eta2", "eta3"]
    eta_ranges = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]

# Load cross-section JSON file
def load_cross_sections(file_path):
    with open(file_path, 'r') as f:
        cross_section_data = json.load(f)
    return cross_section_data

if data == "mc":
    xsec_json_file = f"/eos/user/r/rresendi/cross_sections_{era}.json"
    xsec_data = load_cross_sections(xsec_json_file)

# Load lumi masks and apply them
def load_lumi_mask(file_path):
    with open(file_path, 'r') as f:
        goldenJSONDict = json.load(f)

    def mask(run, luminosityBlock):
        mask_array = np.zeros_like(run, dtype=bool)
        for i in range(len(run)):
            run_str = str(run[i])
            if run_str in goldenJSONDict:
                goodIntervals = goldenJSONDict[run_str]
                for interval in goodIntervals:
                    min_lumi, max_lumi = interval
                    if min_lumi <= luminosityBlock[i] <= max_lumi:
                        mask_array[i] = True
                        break
        return mask_array

    return mask

# Define reference cut function
def passRefCut(ev, era, lumi_mask):
    if not lumi_mask([ev.run], [ev.luminosityBlock])[0]:
        return False

    if era in ["2018", "2017"]:
        cutAnyFilter = (
            ev.Flag_goodVertices
            and ev.Flag_globalSuperTightHalo2016Filter
            and ev.Flag_HBHENoiseFilter
            and ev.Flag_HBHENoiseIsoFilter
            and ev.Flag_EcalDeadCellTriggerPrimitiveFilter
            and ev.Flag_BadPFMuonFilter
            and ev.Flag_BadPFMuonDzFilter
            and ev.Flag_eeBadScFilter
            and ev.Flag_ecalBadCalibFilter
        )
    elif era in ["2016", "2016APV"]:
        cutAnyFilter = (
            ev.Flag_goodVertices
            and ev.Flag_globalSuperTightHalo2016Filter
            and ev.Flag_HBHENoiseFilter
            and ev.Flag_HBHENoiseIsoFilter
            and ev.Flag_EcalDeadCellTriggerPrimitiveFilter
            and ev.Flag_BadPFMuonFilter
            and ev.Flag_BadPFMuonDzFilter
            and ev.Flag_eeBadScFilter
        )
    else:
        raise ValueError("Unsupported era for quality filters")

    return cutAnyFilter

# Create histograms
histos = {}
if etaOption == "Eta":
    for eta_bin in eta_bins:
        for var in histBins:
            if var == "lep1pt":
                histos[f"{eta_bin}_{var}_num"] = ROOT.TH1F(f"{eta_bin}_{var}_num", f"{eta_bin}_{var}_num", len(histBins[var]) - 1, np.array(histBins[var], dtype=np.float32))
                histos[f"{eta_bin}_{var}_den"] = ROOT.TH1F(f"{eta_bin}_{var}_den", f"{eta_bin}_{var}_den", len(histBins[var]) - 1, np.array(histBins[var], dtype=np.float32))
            else:
                histos[f"{eta_bin}_{var}_num"] = ROOT.TH1F(f"{eta_bin}_{var}_num", f"{eta_bin}_{var}_num", histBins[var][0], histBins[var][1], histBins[var][2])
                histos[f"{eta_bin}_{var}_den"] = ROOT.TH1F(f"{eta_bin}_{var}_den", f"{eta_bin}_{var}_den", histBins[var][0], histBins[var][1], histBins[var][2])
else:
    for var in histBins:
        x_label = pt_label if var == "lep1pt" else var
        if var == "lep1pt":
            histos[var + "_num"] = ROOT.TH1F(var + "_num", var + "_num", len(histBins[var]) - 1, lep1pt_bin_edges)
            histos[var + "_den"] = ROOT.TH1F(var + "_den", var + "_den", len(histBins[var]) - 1, lep1pt_bin_edges)
        else:
            histos[var + "_num"] = ROOT.TH1F(var + "_num", var + "_num", histBins[var][0], histBins[var][1], histBins[var][2])
            histos[var + "_den"] = ROOT.TH1F(var + "_den", var + "_den", histBins[var][0], histBins[var][1], histBins[var][2])

def passes_lepton_cuts(ev, lepton, leptonIndex):
    if lepton == "Muon":
        return (
            ev.Muon_tightId[leptonIndex]
            and abs(ev.Muon_eta[leptonIndex]) < 2.4
            and abs(ev.Muon_dz[leptonIndex]) <= 0.05
            and abs(ev.Muon_dxy[leptonIndex]) <= 0.02
            and ev.Muon_pfIsoId[leptonIndex] >= 5)
    else:
        return (
            ev.Electron_cutBased[leptonIndex] >= 2
            and ev.Electron_mvaFall17V2Iso_WP80[leptonIndex]
            and abs(ev.Electron_dxy[leptonIndex]) < 0.05 + 0.05 * (abs(ev.Electron_eta[leptonIndex]) > 1.479)
            and abs(ev.Electron_dz[leptonIndex]) < 0.10 + 0.10 * (abs(ev.Electron_eta[leptonIndex]) > 1.479)
            and ((abs(ev.Electron_eta[leptonIndex]) < 1.444) or (abs(ev.Electron_eta[leptonIndex]) > 1.566))
            and abs(ev.Electron_eta[leptonIndex]) < 2.5)

def passes_jet_cuts(ev, jetIndex):
    return ev.Jet_pt[jetIndex] > 60

# Calculate dPhi and deltaR
def dPhi(obj_phi, jet_phi):
    dphi = obj_phi - jet_phi
    dphi = np.arccos(np.cos(dphi))
    return dphi

def deltaR(eta1, phi1, eta2, phi2):
    deta = eta1 - eta2
    dphi = phi1 - phi2
    dphi = np.arctan2(np.sin(dphi), np.cos(dphi))
    return np.sqrt(deta**2 + dphi**2)

def is_leading_lepton_matched(trigObj_eta, trigObj_phi, trigObj_id, trigObj_filterBits, lepton_eta, lepton_phi, lepton_type):
    matched = False
    for i in range(len(trigObj_id)):
        if lepton_type == "Electron" and abs(trigObj_id[i]) == 11:
            if ((trigObj_filterBits[i] & 2) == 2) or ((trigObj_filterBits[i] & 2048) == 2048) or ((trigObj_filterBits[i] & 8192) == 8192):
                dR = deltaR(lepton_eta, lepton_phi, trigObj_eta[i], trigObj_phi[i])
                if dR < 0.1:
                    matched = True
                    break
        elif lepton_type == "Muon" and abs(trigObj_id[i]) == 13:
            if (((trigObj_filterBits[i] & 2) == 2) or ((trigObj_filterBits[i] & 1024) == 1024)):
                dR = deltaR(lepton_eta, lepton_phi, trigObj_eta[i], trigObj_phi[i])
                if dR < 0.1:
                    matched = True
                    break
    return matched

def get_eta_bin(eta):
    for i, (low, high) in enumerate(eta_ranges):
        if low <= abs(eta) < high:
            return eta_bins[i]
    return None

if data == "data":
    if era in ["2016", "2016APV"]:
        lumi_mask_func = load_lumi_mask("/eos/user/r/rresendi/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt")
    elif era == "2017":
        lumi_mask_func = load_lumi_mask("/eos/user/r/rresendi/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt")
    elif era == "2018":
        lumi_mask_func = load_lumi_mask("/eos/user/r/rresendi/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt")
    else:
        raise ValueError("No era is defined")

print("Starting processing of input files")

inF = 0
nF = len(inputFiles)

for i, iFile in enumerate(inputFiles):
    inF += 1
    print(f"Starting file {inF}/{nF}, {iFile}")
    tf = ROOT.TFile.Open(iFile, "READ")
    if not tf or tf.IsZombie():
        print(f"Error opening file {iFile}. Skipping.")
        continue
    events = tf.Get("Events")
    if not events:
        print(f"No 'Events' tree found in {iFile}. Skipping.")
        tf.Close()
        continue

    # Initialize event weight
    event_weight = 1.0

    if data == "mc":
        # Get total number of events in the sample
        hist_events = tf.Get("nEventsGenWeighted")
        if hist_events:
            n_total_events = hist_events.GetBinContent(1)
        else:
            n_total_events = events.GetEntries()

        # Extract sample name from the original file path
        original_file_path = tf.GetName()
        print(f"Full file path from ROOT: {original_file_path}")  # Debugging print

        if '/mc/' in original_file_path.lower():
            path_parts = original_file_path.split('/')
            try:
                idx = path_parts.index('mc')
                sample_name = path_parts[idx + 2]  # Extract sample name
                print(f"Sample name extracted: {sample_name}")
            
            except (ValueError, IndexError):
                print(f"Could not determine sample name from: {original_file_path}")
                tf.Close()
                continue
        else:
            print(f"'mc' not found in file path: {original_file_path}")
            tf.Close()
            continue

        # Try to find a matching key in xsec_data
        matching_keys = [key for key in xsec_data if sample_name in key]

        if matching_keys:
            matching_key = matching_keys[0]
            cross_section = xsec_data[matching_key]["xsec"]
            print(f"Using cross section {cross_section} for sample '{sample_name}' matched with key '{matching_key}'")
        else:
            print(f"Cross section for {sample_name} not found in JSON file. Skipping this file.")
            tf.Close()
            continue

        # Calculate event weight for MC
        event_weight = (cross_section * luminosity) / n_total_events
        print(f'event weight: {event_weight}')

    iEv = 0
    nEv = events.GetEntries()

    print(f'events have been counted. there are {nEv} events in this file')
    import time
    for ev in events:
        iEv += 1
        # if(iEv % 10 == 0):
        #     print(iEv, nEv, time.time())

        # Apply reference cuts for data early
        if data == "data" and not passRefCut(ev, era, lumi_mask_func):
            continue

        # Check if any HLT path is true early on
        passHLT = False
        for hltpath in hlt:
            if getattr(ev, hltpath, False):
                passHLT = True

        highest_pt = -1
        highest_pt_lepton_index = -1

        # Find the leading lepton
        for leptonIndex in range(getattr(ev, "n" + lepton)):
            if passes_lepton_cuts(ev, lepton, leptonIndex):
                pt = getattr(ev, lepton + "_pt")[leptonIndex]
                if pt > highest_pt:
                    highest_pt = pt
                    highest_pt_lepton_index = leptonIndex

        if highest_pt_lepton_index == -1:
            continue

        lepton_phi = getattr(ev, lepton + "_phi")[highest_pt_lepton_index]
        lepton_eta = getattr(ev, lepton + "_eta")[highest_pt_lepton_index]

        # Find the leading jet
        highest_jet_pt = -1
        highest_jet_pt_index = -1
        for jetIndex in range(ev.nJet):
            if passes_jet_cuts(ev, jetIndex):
                if ev.Jet_pt[jetIndex] > highest_jet_pt:
                    highest_jet_pt = ev.Jet_pt[jetIndex]
                    highest_jet_pt_index = jetIndex

        if highest_jet_pt_index == -1:
            continue

        jet_phi = ev.Jet_phi[highest_jet_pt_index]
        jet_eta = ev.Jet_eta[highest_jet_pt_index]

        # Calculate deltaR and dPhi between the lepton and the leading jet
        if deltaR(lepton_eta, lepton_phi, jet_eta, jet_phi) < 0.5:
            continue
        if dPhi(lepton_phi, jet_phi) < 1.5:
            continue

        # Check MET cuts
        dphi_jetmet = dPhi(ev.MET_phi, jet_phi)
        if dphi_jetmet < 1.5:
            continue

        # Match leading lepton to trigger objects
        lepton_matched = is_leading_lepton_matched(ev.TrigObj_eta, ev.TrigObj_phi, ev.TrigObj_id, ev.TrigObj_filterBits, lepton_eta, lepton_phi, lepton)

        # Calculate boson pT
        boson_ptx = getattr(ev, lepton + "_pt")[highest_pt_lepton_index] * np.cos(lepton_phi) + ev.MET_pt * np.cos(ev.MET_phi)
        boson_pty = getattr(ev, lepton + "_pt")[highest_pt_lepton_index] * np.sin(lepton_phi) + ev.MET_pt * np.sin(ev.MET_phi)
        boson_pt = np.sqrt(boson_ptx**2 + boson_pty**2)

        # Variables you want to study
        passmetCut = ev.MET_pt >= offlineCuts["MET"]
        passlepCut = getattr(ev, lepton + "_pt")[highest_pt_lepton_index] >= offlineCuts["lep1pt"]
        dphi = dPhi(lepton_phi, ev.MET_phi)
        mT = np.sqrt(2 * highest_pt * ev.MET_pt * (1 - np.cos(dphi)))
        passmtCut = offlineCuts["mT"][0] < mT < offlineCuts["mT"][1]
        passbosonCut = offlineCuts["Boson pT"] < boson_pt

        # Fill histograms
        if etaOption == "Eta":
            eta_bin = get_eta_bin(lepton_eta)
            if eta_bin is None:
                continue

            for var in histBins:
                passDen = False
                fillvar = None
                if var == "lep1pt":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passmetCut and passmtCut and passbosonCut
                    fillvar = highest_pt
                elif var == "MET":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passlepCut and passmtCut and passbosonCut
                    fillvar = ev.MET_pt
                elif var == "mT":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passlepCut and passmetCut and passbosonCut
                    fillvar = mT
                elif var == "lep1phi":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passmetCut and passmtCut and passlepCut and passbosonCut
                    fillvar = lepton_phi
                elif var == "MET phi":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passmetCut and passmtCut and passlepCut and passbosonCut
                    fillvar = ev.MET_phi
                elif var == "Boson pT":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passmetCut and passmtCut and passlepCut
                    fillvar = boson_pt

                # Fill denominator histogram with weight
                if data == "data":
                    if getattr(ev, refhlt, False):
                        if passDen and fillvar is not None:
                            histos[f"{eta_bin}_{var}_den"].Fill(fillvar, event_weight)

                            # Fill numerator histogram based on HLT or lepton matching criteria, apply weight
                            if passHLT and lepton_matched:
                                histos[f"{eta_bin}_{var}_num"].Fill(fillvar, event_weight)
                else:
                    if passDen and fillvar is not None:
                        histos[f"{eta_bin}_{var}_den"].Fill(fillvar, event_weight)

                        # Fill numerator histogram based on HLT or lepton matching criteria, apply weight
                        if passHLT and lepton_matched:
                            histos[f"{eta_bin}_{var}_num"].Fill(fillvar, event_weight)

        else:
            for var in histBins:
                passDen = False
                fillvar = None
                if var == "lep1pt":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passmetCut and passmtCut and passbosonCut
                    fillvar = highest_pt
                elif var == "MET":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passlepCut and passmtCut and passbosonCut
                    fillvar = ev.MET_pt
                elif var == "mT":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passlepCut and passmetCut and passbosonCut
                    fillvar = mT
                elif var == "lep1phi":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passmetCut and passmtCut and passlepCut and passbosonCut
                    fillvar = lepton_phi
                elif var == "MET phi":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passmetCut and passmtCut and passlepCut and passbosonCut
                    fillvar = ev.MET_phi
                elif var == "Boson pT":
                    passDen = passes_lepton_cuts(ev, lepton, highest_pt_lepton_index) and passmetCut and passmtCut and passlepCut
                    fillvar = boson_pt

                # Fill denominator histogram with weight
                if data == "data":
                    if getattr(ev, refhlt, False):
                        if passDen and fillvar is not None:
                            histos[var + "_den"].Fill(fillvar, event_weight)

                            # Fill numerator histogram based on HLT or lepton matching criteria, apply weight
                            if passHLT and lepton_matched:
                                histos[var + "_num"].Fill(fillvar, event_weight)
                
                else:
                    if passDen and fillvar is not None:
                            histos[var + "_den"].Fill(fillvar, event_weight)

                            # Fill numerator histogram based on HLT or lepton matching criteria, apply weight
                            if passHLT and lepton_matched:
                                histos[var + "_num"].Fill(fillvar, event_weight)
                        
    tf.Close()

# Now calculate efficiencies and adjust the event weights
print("Calculating efficiencies and adjusting histogram contents")
outF = ROOT.TFile(outputHistos, "RECREATE")
if etaOption == "Eta":
    for var in histBins:
        for eta_bin in eta_bins:
            num_hist = histos[f"{eta_bin}_{var}_num"]
            den_hist = histos[f"{eta_bin}_{var}_den"]
            eff_hist = num_hist.Clone(f"{eta_bin}_{var}_eff")
            eff_hist.Divide(den_hist)
            eff_hist.Write()
            print(f"Number of events in the denominator for {eta_bin}_{var}: {den_hist.GetEntries()}")
            print(f"Number of events passing in the numerator for {eta_bin}_{var}: {num_hist.GetEntries()}")
else:
    for var in histBins:
        num_hist = histos[var + "_num"]
        den_hist = histos[var + "_den"]
        eff_hist = num_hist.Clone(var + "_eff")
        eff_hist.Divide(den_hist)
        eff_hist.Write()
        print(f"Number of events in the denominator for {var}: {den_hist.GetEntries()}")
        print(f"Number of events passing in the numerator for {var}: {num_hist.GetEntries()}")

for h in histos:
    histos[h].Write()
outF.Close()

print("Processing complete. Output written to %s" % outputHistos)
