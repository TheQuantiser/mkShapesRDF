#!/usr/bin/env bash

# CERN LXPLUS analysis preset:
# - selects the shared-checkout production stage-out profile
# - keeps only identity/output conveniences in the shell wrapper

export EXECUTION_PROFILE="${EXECUTION_PROFILE:-shared_xrootd_eos_production}"
export SITE_PRESET="${SITE_PRESET:-lxplus}"
export XRD_WRITE_ENDPOINT="${XRD_WRITE_ENDPOINT:-root://eoscms.cern.ch}"
export EOS_USER="${EOS_USER:-${CERN_USER:-${USER}}}"
export PRODUCTION_CAMPAIGN="${PRODUCTION_CAMPAIGN:-${SITE_PRESET}}"
