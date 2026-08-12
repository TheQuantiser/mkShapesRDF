#!/usr/bin/env bash
# CERN shared-checkout and input, with FNAL EOS stage-out.
export INPUT_ACCESS_MODE="xrootd"
export CONDOR_RUNTIME_PACKAGE="0"
export USE_X509_PROXY="1"
export XRD_READ_ENDPOINT="root://eoscms.cern.ch"
export XRD_DISCOVERY_ENDPOINT="root://eoscms.cern.ch"
export XRD_WRITE_ENDPOINT="root://cmseos.fnal.gov"
export EOS_USER="${FNAL_USER:-${CERN_USER:-${USER}}}"
