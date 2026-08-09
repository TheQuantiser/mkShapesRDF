#!/usr/bin/env bash

# FNAL CMS LPC packaged analysis preset:
# - selects the packaged production stage-out profile
# - keeps only identity/output conveniences in the shell wrapper

export EXECUTION_PROFILE="${EXECUTION_PROFILE:-packaged_fnal_xrootd_eos_production}"
export SITE_PRESET="${SITE_PRESET:-fnal_lpc_packaged}"
export XRD_WRITE_ENDPOINT="${XRD_WRITE_ENDPOINT:-root://cmseos.fnal.gov}"
export EOS_USER="${EOS_USER:-${CERN_USER:-${USER}}}"
export PRODUCTION_CAMPAIGN="${PRODUCTION_CAMPAIGN:-${SITE_PRESET}}"

# The generic submitter intentionally remains site-neutral.  LPC removes jobs
# that exceed its 2100 MB default, while the full histogram graph needs more
# headroom.  HTCondor's documented environment override mechanism adds this
# submit attribute without changing mkShapesRDF core or its generated JDL.
export _CONDOR_REQUESTMEMORY="${_CONDOR_REQUESTMEMORY:-4096}"
case " ${_CONDOR_SUBMIT_ATTRS:-} " in
  *" RequestMemory "*) ;;
  *) export _CONDOR_SUBMIT_ATTRS="${_CONDOR_SUBMIT_ATTRS:+${_CONDOR_SUBMIT_ATTRS} }RequestMemory" ;;
esac
