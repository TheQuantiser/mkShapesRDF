#!/usr/bin/env bash
# FNAL LPC packaged workers, direct CERN XRootD input and FNAL EOS output.
export INPUT_ACCESS_MODE="xrootd"
export CONDOR_RUNTIME_PACKAGE="1"
export USE_X509_PROXY="1"
export XRD_READ_ENDPOINT="root://eoscms.cern.ch"
export XRD_DISCOVERY_ENDPOINT="root://eoscms.cern.ch"
export XRD_WRITE_ENDPOINT="root://cmseos.fnal.gov"
export EOS_USER="${FNAL_USER:-${USER}}"
