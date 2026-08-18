#!/usr/bin/env bash

# CERN LXPLUS shared-checkout analysis preset with FNAL stage-out:
# - submits workers from the CERN checkout without a Condor runtime package
# - reads CERN inputs directly through XRootD
# - stages production output to the FNAL CMS Store endpoint
# - EOS_USER (or FNAL_USER) must name the owner of the FNAL /store/user area
# - resets the complete site contract when sourced; override afterward if needed

export EXECUTION_PROFILE="shared_xrootd_fnal_eos_production"
export INPUT_ACCESS_MODE="xrootd"
export OUTPUT_MODE="production-remote"
export CONDOR_RUNTIME_PACKAGE="0"
export CONFIG_INCLUDE_BASE="checkout"
export USE_X509_PROXY="1"
export XRD_READ_ENDPOINT="root://eoscms.cern.ch"
export XRD_DISCOVERY_ENDPOINT="root://eoscms.cern.ch"
export SITE_PRESET="lxplus"
export XRD_WRITE_ENDPOINT="root://cmseos.fnal.gov"
export EOS_USER="${FNAL_USER:-${CERN_USER:-${USER}}}"
export PRODUCTION_CAMPAIGN="lxplus_fnal"
