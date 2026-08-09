#!/usr/bin/env bash

# FNAL CMS LPC packaged analysis preset:
# - selects the packaged production stage-out profile
# - keeps only identity/output conveniences in the shell wrapper

export EXECUTION_PROFILE="${EXECUTION_PROFILE:-packaged_fnal_stagein_eos_production}"
export INPUT_ACCESS_MODE="${INPUT_ACCESS_MODE:-stage-in}"
export XRD_READ_ENDPOINT="${XRD_READ_ENDPOINT:-root://eoscms.cern.ch}"
export XRD_DISCOVERY_ENDPOINT="${XRD_DISCOVERY_ENDPOINT:-root://eoscms.cern.ch}"
export SITE_PRESET="${SITE_PRESET:-fnal_lpc_packaged}"
export XRD_WRITE_ENDPOINT="${XRD_WRITE_ENDPOINT:-root://cmseos.fnal.gov}"
export EOS_USER="${EOS_USER:-${CERN_USER:-${USER}}}"
export PRODUCTION_CAMPAIGN="${PRODUCTION_CAMPAIGN:-${SITE_PRESET}}"
