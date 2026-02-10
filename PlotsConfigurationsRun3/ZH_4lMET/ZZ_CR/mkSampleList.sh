#!/usr/bin/env bash
set -euo pipefail

BASE="/eos/cms/store/group/phys_higgs/cmshww"
OUT="cmshww_HWWNano_part0_22to25.txt"
VERBOSE=1

tmp_nom="$(mktemp)"
tmp_syst="$(mktemp)"

dirs_visited=0
files_found=0
nom_found=0
syst_found=0

log() { [[ "$VERBOSE" -eq 1 ]] && printf "%s\n" "$*" >&2 || true; }

eos_exists() { eos ls "$1" >/dev/null 2>&1; }

# subdirs only (names)
eos_list_dirs() {
  local d="$1"
  eos ls -l "$d" 2>/dev/null | awk '$1 ~ /^d/ {print $NF}'
}

# files only (names) -- eos ls -l marks dirs with d, everything else treated as file
eos_list_files() {
  local d="$1"
  eos ls -l "$d" 2>/dev/null | awk '$1 !~ /^d/ {print $NF}'
}

# DFS that ALWAYS walks entire subtree; collects *__part0.root wherever it appears.
crawl_collect_part0() {
  local d="$1"
  local depth="${2:-0}"
  local indent
  indent="$(printf "%*s" $((2*depth)) "")"

  dirs_visited=$((dirs_visited + 1))
  (( depth <= 2 )) && log "${indent}↳ $d"

  # Collect part0 files in *this* directory (if any)
  local f
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
      if [[ "$f" =~ __part0\.root$ ]]; then
        full="$d/$f"
        files_found=$((files_found + 1))

        # Systematics: token appears anywhere in the path (embedded in dirname)
        if [[ "$full" =~ (do_suffix|up_suffix) ]]; then
          syst_found=$((syst_found + 1))
          printf "%s\n" "$full" >> "$tmp_syst"
        else
          nom_found=$((nom_found + 1))
          printf "%s\n" "$full" >> "$tmp_nom"
        fi
      fi

  done < <(eos_list_files "$d")

  # Recurse into ALL subdirectories
  local sub
  while IFS= read -r sub; do
    [[ -z "$sub" ]] && continue
    crawl_collect_part0 "$d/$sub" $((depth+1))
  done < <(eos_list_dirs "$d")
}

log "Scanning users under: $BASE"
log "Output: $OUT"
log ""

while IFS= read -r user; do
  [[ -z "$user" ]] && continue

  # optional skip noise dirs
  [[ "$user" =~ ^(TO_DELETE|crab3checkwrite_) ]] && { log "[skip] $user"; continue; }

  hwwnano="$BASE/$user/HWWNano"
  eos_exists "$hwwnano" || { log "[no HWWNano] $user"; continue; }

  log "============================================================"
  log "[user] $user"

  while IFS= read -r camp; do
    [[ -z "$camp" ]] && continue
    [[ "$camp" =~ (22|23|24|25) ]] || continue

    campdir="$hwwnano/$camp"
    log "  ----------------------------------------------------------"
    log "  [campaign] $camp"
    log "    root: $campdir"

    before_files=$files_found
    before_syst=$syst_found
    before_nom=$nom_found

    crawl_collect_part0 "$campdir" 0

    log "    [campaign done] +$((files_found-before_files)) files (nom +$((nom_found-before_nom)), syst +$((syst_found-before_syst)))"
  done < <(eos_list_dirs "$hwwnano")

done < <(eos_list_dirs "$BASE")

log ""
log "Finalizing..."
{
  LC_ALL=C sort -u "$tmp_nom"
  echo
  LC_ALL=C sort -u "$tmp_syst"
} > "$OUT"

rm -f "$tmp_nom" "$tmp_syst"

log "Visited directories: $dirs_visited"
log "Found part0 files : $files_found (nom=$nom_found, syst=$syst_found)"
echo "Wrote: $OUT"
