#!/usr/bin/env bash
set -euo pipefail

BASE="/eos/cms/store/group/phys_higgs/cmshww"
OUT="cmshww_HWWNano_file_list_22to25.txt"

P="${P:-8}"
RETRY="${RETRY:-4}"
BACKOFF0="${BACKOFF0:-0.2}"
TICK="${TICK:-0.5}"
VERBOSE="${VERBOSE:-1}"

ts() { date +"%H:%M:%S"; }

# --- robust integers ------------------------------------------------------
num_only(){ local x="${1:-}"; x="${x//[^0-9]/}"; [[ -n "$x" ]] && printf "%s" "$x" || printf "0"; }
fget(){ [[ -f "$1" ]] && num_only "$(cat "$1" 2>/dev/null || true)" || printf "0"; }
fset(){ printf "%s" "$(num_only "$2")" > "$1"; }
fincr(){ local f="$1"; local v; v="$(fget "$f")"; fset "$f" "$((v+1))"; }

# --- EOS ------------------------------------------------------------------
eos_ls(){
  local args=("$@") i=0 backoff="$BACKOFF0"
  while (( i <= RETRY )); do
    eos ls "${args[@]}" 2>/dev/null && return 0
    ((i++)) || true
    sleep "$backoff" || true
    backoff=$(awk -v b="$backoff" 'BEGIN{printf "%.3f",(b*2)}')
  done
  return 1
}
eos_exists(){ eos_ls "$1" >/dev/null; }
eos_dirs(){ eos_ls -l "$1" | awk '$1 ~ /^d/ {print $NF}'; }
eos_files(){ eos_ls -l "$1" | awk '$1 !~ /^d/ {print $NF}'; }

is_syst_path(){ [[ "$1" =~ (do|up)_suffix ]]; }

# leaf: no subdirs; if subdir listing fails, treat as leaf so we still attempt file listing
is_leaf_dir(){
  local d="$1"
  if eos_dirs "$d" >/dev/null 2>&1; then
    ! eos_dirs "$d" | head -n 1 | grep -q .
  else
    return 0
  fi
}

# --- shared state ---------------------------------------------------------
STATE="$(mktemp -d)"
ALL="$STATE/all.tagged"
ERR="$STATE/errors.log"
touch "$ALL" "$ERR"

C_NOM="$STATE/c_nom"; fset "$C_NOM" 0
C_SYST="$STATE/c_syst"; fset "$C_SYST" 0
C_USERS_DONE="$STATE/c_users_done"; fset "$C_USERS_DONE" 0
C_USERS_TOTAL="$STATE/c_users_total"; fset "$C_USERS_TOTAL" 0
C_CAMPS_DONE="$STATE/c_camps_done"; fset "$C_CAMPS_DONE" 0
C_DIRS="$STATE/c_dirs"; fset "$C_DIRS" 0

wfile(){ printf "%s/w.%s" "$STATE" "$1"; }
set_wstatus(){
  local pid="$1" u="$2" c="$3" d="$4"
  d="${d//$'\e'/}"               # strip ESC
  printf "u=%s c=%s d=%s\n" "$u" "$c" "$d" > "$(wfile "$pid")"
}

status_line(){
  [[ "$VERBOSE" -eq 1 ]] || return 0
  printf "\r[%s] %s" "$(ts)" "$*" >&2
}
finish_status(){
  [[ "$VERBOSE" -eq 1 ]] || return 0
  printf "\n" >&2
}

# --- crawl ---------------------------------------------------------------
crawl_campaign(){ # user camp root pid
  local user="$1" camp="$2" root="$3" pid="$4"
  local -a stack=("$root")
  local d sub

  while ((${#stack[@]})); do
    d="${stack[-1]}"; unset 'stack[-1]'
    fincr "$C_DIRS"
    set_wstatus "$pid" "$user" "$camp" "${d#${BASE}/}"

    if is_leaf_dir "$d"; then
      eos_files "$d" \
        | grep -E '__part0\.root$' \
        | while IFS= read -r f; do
            [[ -z "$f" ]] && continue
            local full="$d/$f"
            if is_syst_path "$full"; then
              fincr "$C_SYST"; printf "S\t%s\n" "$full" >> "$ALL"
            else
              fincr "$C_NOM";  printf "N\t%s\n" "$full" >> "$ALL"
            fi
          done || true
      continue
    fi

    while IFS= read -r sub; do
      [[ -z "$sub" ]] && continue
      stack+=("$d/$sub")
    done < <(eos_dirs "$d" | LC_ALL=C sort)
  done
}

worker_user(){ # user
  local user="$1" pid="$$"
  [[ "$user" =~ ^(TO_DELETE|crab3checkwrite_) ]] && exit 0
  local hww="$BASE/$user/HWWNano"
  eos_exists "$hww" || exit 0

  local camp cdir
  while IFS= read -r camp; do
    [[ -z "$camp" ]] && continue
    [[ "$camp" =~ (22|23|24|25) ]] || continue
    cdir="$hww/$camp"
    fincr "$C_CAMPS_DONE"
    crawl_campaign "$user" "$camp" "$cdir" "$pid" 2>>"$ERR" || true
  done < <(eos_dirs "$hww" | LC_ALL=C sort)

  fincr "$C_USERS_DONE"
  set_wstatus "$pid" "$user" "-" "DONE"
  exit 0
}

export -f num_only fget fset fincr eos_ls eos_exists eos_dirs eos_files is_syst_path is_leaf_dir wfile set_wstatus crawl_campaign worker_user
export BASE RETRY BACKOFF0 STATE ALL ERR C_NOM C_SYST C_USERS_DONE C_USERS_TOTAL C_CAMPS_DONE C_DIRS

monitor(){
  [[ "$VERBOSE" -eq 1 ]] || return 0
  while [[ ! -f "$STATE/STOP" ]]; do
    local nom syst ud ut cd dirs
    nom="$(fget "$C_NOM")"
    syst="$(fget "$C_SYST")"
    ud="$(fget "$C_USERS_DONE")"
    ut="$(fget "$C_USERS_TOTAL")"
    cd="$(fget "$C_CAMPS_DONE")"
    dirs="$(fget "$C_DIRS")"

    # pick most recently updated worker status (not the first one)
    local w s
    w="$(ls -t "$STATE"/w.* 2>/dev/null | head -n 1 || true)"
    s="$( [[ -n "$w" ]] && tail -n 1 "$w" 2>/dev/null || echo "u=? c=? d=?" )"

    status_line "$s | nom=$nom syst=$syst users=$ud/$ut camps~=$cd dirs=$dirs"
    sleep "$TICK" || true
  done
}

# --- main ---------------------------------------------------------------
users="$STATE/users"
eos_dirs "$BASE" | LC_ALL=C sort > "$users"
ut="$(num_only "$(wc -l < "$users")")"
fset "$C_USERS_TOTAL" "$ut"

[[ "$VERBOSE" -eq 1 ]] && {
  printf "[%s] base=%s  users=%s  P=%s  retry=%s  tick=%ss\n" "$(ts)" "$BASE" "$ut" "$P" "$RETRY" "$TICK" >&2
  printf "[%s] writing to: %s\n" "$(ts)" "$OUT" >&2
}

monitor & mon_pid=$!

# IMPORTANT: no "-n" when using -I (avoids your warning)
cat "$users" \
  | xargs -P "$P" -I{} bash -c 'worker_user "$@"' _ {} \
  2>>"$ERR" || true

touch "$STATE/STOP"
wait "$mon_pid" 2>/dev/null || true
finish_status

nom="$STATE/nom"; syst="$STATE/syst"
awk -F'\t' '$1=="N"{print $2}' "$ALL" | LC_ALL=C sort -u > "$nom"
awk -F'\t' '$1=="S"{print $2}' "$ALL" | LC_ALL=C sort -u > "$syst"

{ cat "$nom"; echo; cat "$syst"; } > "$OUT"

n_nom="$(num_only "$(wc -l < "$nom")")"
n_syst="$(num_only "$(wc -l < "$syst")")"

printf "Wrote: %s\nNominal: %s  Systematics: %s\nErrors: %s\n" "$OUT" "$n_nom" "$n_syst" "$ERR"
