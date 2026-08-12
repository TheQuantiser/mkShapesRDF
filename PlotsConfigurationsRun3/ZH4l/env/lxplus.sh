#!/usr/bin/env bash
# CERN shared-checkout, direct CERN XRootD input and CERN EOS output.
export INPUT_ACCESS_MODE="xrootd"
export CONDOR_RUNTIME_PACKAGE="0"
export USE_X509_PROXY="1"
export XRD_READ_ENDPOINT="root://eoscms.cern.ch"
export XRD_DISCOVERY_ENDPOINT="root://eoscms.cern.ch"
export XRD_WRITE_ENDPOINT="root://eoscms.cern.ch"
export EOS_USER="${CERN_USER:-${USER}}"
