#!/usr/bin/env bash

# FNAL CMS LPC packaged analysis preset:
# - reads CERN inputs directly through XRootD
# - stages outputs to FNAL EOS
# - resets the complete site contract when sourced; override afterward if needed

export EXECUTION_PROFILE="packaged_fnal_xrootd_eos_production"
export INPUT_ACCESS_MODE="xrootd"
export OUTPUT_MODE="production-remote"
export CONDOR_RUNTIME_PACKAGE="1"
export CONFIG_INCLUDE_BASE="runtime"
export USE_X509_PROXY="1"
export XRD_READ_ENDPOINT="root://eoscms.cern.ch"
export XRD_DISCOVERY_ENDPOINT="root://eoscms.cern.ch"
export SITE_PRESET="fnal_lpc_packaged"
export XRD_WRITE_ENDPOINT="root://cmseos.fnal.gov"
export EOS_USER="${FNAL_USER:-${CERN_USER:-${USER}}}"
export PRODUCTION_CAMPAIGN="fnal_lpc_packaged"
