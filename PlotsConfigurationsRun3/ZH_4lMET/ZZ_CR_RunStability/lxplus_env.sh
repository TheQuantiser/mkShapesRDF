#!/usr/bin/env bash

# CERN LXPLUS analysis preset:
# - selects the shared-checkout production stage-out profile
# - resets the complete site contract when sourced; override afterward if needed

export EXECUTION_PROFILE="shared_xrootd_eos_production"
export INPUT_ACCESS_MODE="xrootd"
export OUTPUT_MODE="production-remote"
export CONDOR_RUNTIME_PACKAGE="0"
export CONFIG_INCLUDE_BASE="checkout"
export USE_X509_PROXY="1"
export XRD_READ_ENDPOINT="root://eoscms.cern.ch"
export XRD_DISCOVERY_ENDPOINT="root://eoscms.cern.ch"
export SITE_PRESET="lxplus"
export XRD_WRITE_ENDPOINT="root://eoscms.cern.ch"
export EOS_USER="${CERN_USER:-${USER}}"
export PRODUCTION_CAMPAIGN="lxplus"
