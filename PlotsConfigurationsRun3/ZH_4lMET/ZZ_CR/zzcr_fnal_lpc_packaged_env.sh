#!/usr/bin/env bash

# FNAL CMS LPC packaged Condor preset:
# - selects the packaged production stage-out profile
# - keeps only identity/output conveniences in the shell wrapper

export ZZCR_EXECUTION_PROFILE="${ZZCR_EXECUTION_PROFILE:-packaged_xrootd_eos_production}"
export ZZCR_SITE_PRESET="${ZZCR_SITE_PRESET:-fnal_lpc_packaged}"
export ZZCR_EOS_USER="${ZZCR_EOS_USER:-${CERN_USER:-${USER}}}"
export ZZCR_PRODUCTION_CAMPAIGN="${ZZCR_PRODUCTION_CAMPAIGN:-${ZZCR_SITE_PRESET}}"
