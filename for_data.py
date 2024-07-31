# met filter:

def qualityFiltersSelection(events, era: str):
    ### Apply MET filter selection (see https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETOptionalFiltersRun2)
    if era == "2018" or era == "2017":
        cutAnyFilter = (
            (events.Flag.goodVertices)
            & (events.Flag.globalSuperTightHalo2016Filter)
            & (events.Flag.HBHENoiseFilter)
            & (events.Flag.HBHENoiseIsoFilter)
            & (events.Flag.EcalDeadCellTriggerPrimitiveFilter)
            & (events.Flag.BadPFMuonFilter)
            & (events.Flag.BadPFMuonDzFilter)
            & (events.Flag.eeBadScFilter)
            & (events.Flag.ecalBadCalibFilter)
        )
    if era == "2016" or era == "2016apv":
        cutAnyFilter = (
            (events.Flag.goodVertices)
            & (events.Flag.globalSuperTightHalo2016Filter)
            & (events.Flag.HBHENoiseFilter)
            & (events.Flag.HBHENoiseIsoFilter)
            & (events.Flag.EcalDeadCellTriggerPrimitiveFilter)
            & (events.Flag.BadPFMuonFilter)
            & (events.Flag.BadPFMuonDzFilter)
            & (events.Flag.eeBadScFilter)
        )
    return events[cutAnyFilter]

# lumi mask:

from coffea import lumi_tools


def applyGoldenJSON(self, events):
    if (self.era == "2016" or self.era == "2016apv") and self.scouting != 1:
        LumiJSON = lumi_tools.LumiMask(
            "data/GoldenJSON/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt"
        )
    elif self.era == "2016" and self.scouting == 1:
        LumiJSON = lumi_tools.LumiMask(
            "data/GoldenJSON/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON_scout.txt"
        )
    elif self.era == "2016apv" and self.scouting == 1:
        LumiJSON = lumi_tools.LumiMask(
            "data/GoldenJSON/Cert_271036-284044_13TeV_Legacy2016_Collisions16APV_JSON_scout.txt"
        )
    elif self.era == "2017":
        LumiJSON = lumi_tools.LumiMask(
            "data/GoldenJSON/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt"
        )
    elif self.era == "2018":
        LumiJSON = lumi_tools.LumiMask(
            "data/GoldenJSON/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"
        )
    else:
        print("No era is defined. Please specify the year")

    if self.scouting == 1:
        events = events[LumiJSON(events.run, events.lumSec)]
    else:
        events = events[LumiJSON(events.run, events.luminosityBlock)]

    return events

# met reference trigger and cut:
hlt = HLT_PFMETNoMu120_PFMHTNoMu120_IDTight
met_cut = 120