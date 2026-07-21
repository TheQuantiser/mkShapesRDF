#!/usr/bin/env bash
set -Eeuo pipefail

# Defaults can be overridden for testing or alternate EOS areas.
BASE="${BASE:-/eos/cms/store/group/phys_higgs/cmshww}"
OUT="${OUT:-$(date +%Y_%m_%d)_cmshww_HWWNano_file_list_22to25.txt}"
EOS_BIN="${EOS_BIN:-eos}"

P="${P:-8}"
RETRY="${RETRY:-4}"
BACKOFF0="${BACKOFF0:-0.5}"
VERBOSE="${VERBOSE:-1}"

# This EOS client uses egrep/ERE syntax for --name, not shell globs.
# [.] avoids backslash-escaping ambiguity while matching a literal dot.
FIND_NAME_REGEX="${FIND_NAME_REGEX:-.*__part0[.]root$}"

STATE="$(mktemp -d)"
ERR="${ERR:-${OUT%.txt}.errors.log}"

USERS_RAW="$STATE/users.raw"
USERS="$STATE/users.txt"
CAMPAIGNS="$STATE/campaigns.txt"
ALL="$STATE/all.paths"
NOM="$STATE/nominal.paths"
SYST="$STATE/systematic.paths"
FINAL="$STATE/final.txt"

mkdir -p "$STATE/discovery" "$STATE/results" "$STATE/failures"
: > "$ERR"

cleanup() {
    rm -rf "$STATE"
}
trap cleanup EXIT

ts() {
    date +"%H:%M:%S"
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_uint() {
    local name="$1" value="$2"
    [[ "$value" =~ ^[0-9]+$ ]] || die "$name must be a non-negative integer; got: $value"
}

validate_configuration() {
    require_uint P "$P"
    require_uint RETRY "$RETRY"
    require_uint VERBOSE "$VERBOSE"
    (( P >= 1 )) || die "P must be at least 1"

    command -v "$EOS_BIN" >/dev/null 2>&1 || die "EOS executable not found: $EOS_BIN"

    # EOS rejects an ERE beginning with a repetition operator, even though
    # GNU grep may accept some such patterns with only a warning.
    case "$FIND_NAME_REGEX" in
        ['*+?']*|'{'*)
            die "FIND_NAME_REGEX is invalid for EOS ERE matching: $FIND_NAME_REGEX"
            ;;
    esac

    # Validate the intended positive and negative matches locally before
    # issuing dozens of EOS requests.
    if ! printf '%s\n' 'sample__part0.root' | grep -Eq "$FIND_NAME_REGEX" 2>/dev/null; then
        die "FIND_NAME_REGEX is invalid or does not match sample__part0.root: $FIND_NAME_REGEX"
    fi

    if printf '%s\n' 'sample__part0Xroot' | grep -Eq "$FIND_NAME_REGEX" 2>/dev/null; then
        die "FIND_NAME_REGEX is too broad; it must require the literal .root suffix: $FIND_NAME_REGEX"
    fi
}

double_backoff() {
    awk -v value="$1" 'BEGIN { printf "%.3f", value * 2 }'
}

hash_id() {
    printf '%s' "$1" | cksum | awk '{print $1}'
}

log_failure() {
    local description="$1" stderr_file="$2"
    {
        printf '[%s] %s\n' "$(ts)" "$description"
        [[ ! -s "$stderr_file" ]] || sed 's/^/    /' "$stderr_file"
    } >> "$ERR"
}

# Shallow listing. -F marks directories with a trailing slash.
eos_ls_capture() {
    local outfile="$1" path="$2"
    local attempt backoff="$BACKOFF0" tmpout tmperr rc=1

    for ((attempt = 0; attempt <= RETRY; attempt++)); do
        tmpout="${outfile}.out.${BASHPID}.${attempt}"
        tmperr="${outfile}.err.${BASHPID}.${attempt}"
        rm -f "$tmpout" "$tmperr"

        if "$EOS_BIN" ls -F "$path" >"$tmpout" 2>"$tmperr"; then
            mv -f "$tmpout" "$outfile"
            rm -f "$tmperr"
            return 0
        else
            rc=$?
        fi

        if (( attempt == RETRY )); then
            log_failure "FAILED rc=$rc: $EOS_BIN ls -F $path" "$tmperr"
            rm -f "$tmpout" "$tmperr"
            return "$rc"
        fi

        rm -f "$tmpout" "$tmperr"
        sleep "$backoff"
        backoff="$(double_backoff "$backoff")"
    done

    return 1
}

# Recursive file query.
# Return 75 when EOS truncates the result; the caller then subdivides the tree.
eos_find_capture() {
    local outfile="$1" root="$2"
    local attempt backoff="$BACKOFF0" tmpout tmperr rc=1

    for ((attempt = 0; attempt <= RETRY; attempt++)); do
        tmpout="${outfile}.out.${BASHPID}.${attempt}"
        tmperr="${outfile}.err.${BASHPID}.${attempt}"
        rm -f "$tmpout" "$tmperr"

        if "$EOS_BIN" find \
            -f \
            --name "$FIND_NAME_REGEX" \
            "$root" \
            >"$tmpout" 2>"$tmperr"
        then
            rc=0
        else
            rc=$?
        fi

        # Truncation is deterministic for this subtree. Never retry it unchanged.
        if grep -Eqi 'Result is truncated|results are limited' "$tmperr"; then
            rm -f "$tmpout" "$tmperr"
            return 75
        fi

        if (( rc == 0 )); then
            mv -f "$tmpout" "$outfile"
            rm -f "$tmperr"
            return 0
        fi

        if (( attempt == RETRY )); then
            log_failure \
                "FAILED rc=$rc: $EOS_BIN find -f --name '$FIND_NAME_REGEX' $root" \
                "$tmperr"
            rm -f "$tmpout" "$tmperr"
            return "$rc"
        fi

        rm -f "$tmpout" "$tmperr"
        sleep "$backoff"
        backoff="$(double_backoff "$backoff")"
    done

    return 1
}

# Search one subtree. If EOS truncates it, list one level and recurse into children.
crawl_tree() {
    local root="$1" sink="$2"
    local found listing rc entry stripped child name

    found="$(mktemp "$STATE/find.${BASHPID}.XXXXXX")"

    if eos_find_capture "$found" "$root"; then
        awk 'NF' "$found" >> "$sink"
        rm -f "$found"
        return 0
    else
        rc=$?
    fi
    rm -f "$found"

    (( rc == 75 )) || return "$rc"

    (( VERBOSE < 1 )) || printf '[%s] EOS limit reached; splitting: %s\n' "$(ts)" "$root" >&2

    listing="$(mktemp "$STATE/list.${BASHPID}.XXXXXX")"
    if ! eos_ls_capture "$listing" "$root"; then
        rm -f "$listing"
        return 1
    fi

    while IFS= read -r entry; do
        entry="${entry%$'\r'}"
        [[ -n "$entry" ]] || continue

        if [[ "$entry" == */ ]]; then
            stripped="${entry%/}"
            if [[ "$stripped" == /* ]]; then
                child="$stripped"
            else
                child="${root%/}/$stripped"
            fi

            if ! crawl_tree "$child" "$sink"; then
                rm -f "$listing"
                return 1
            fi
            continue
        fi

        # A split directory can contain matching files directly as well as children.
        name="${entry##*/}"
        if printf '%s\n' "$name" | grep -Eq "$FIND_NAME_REGEX"; then
            if [[ "$entry" == /* ]]; then
                printf '%s\n' "$entry" >> "$sink"
            else
                printf '%s/%s\n' "${root%/}" "$entry" >> "$sink"
            fi
        fi
    done < "$listing"

    rm -f "$listing"
}

discover_user() {
    local user="$1" id user_listing hww_listing output
    local entry stripped name campaign have_hww=0

    [[ "$user" =~ ^(TO_DELETE|crab3checkwrite_) ]] && return 0

    id="$(hash_id "$user")"
    user_listing="$STATE/discovery/user.${id}.raw"
    hww_listing="$STATE/discovery/hww.${id}.raw"
    output="$STATE/discovery/campaigns.${id}.txt"

    if ! eos_ls_capture "$user_listing" "$BASE/$user"; then
        touch "$STATE/failures/discovery.${id}"
        return 1
    fi

    while IFS= read -r entry; do
        entry="${entry%$'\r'}"
        [[ "$entry" == */ ]] || continue
        stripped="${entry%/}"
        name="${stripped##*/}"
        if [[ "$name" == HWWNano ]]; then
            have_hww=1
            break
        fi
    done < "$user_listing"

    (( have_hww )) || return 0

    if ! eos_ls_capture "$hww_listing" "$BASE/$user/HWWNano"; then
        touch "$STATE/failures/discovery.${id}"
        return 1
    fi

    : > "$output"
    while IFS= read -r entry; do
        entry="${entry%$'\r'}"
        [[ "$entry" == */ ]] || continue
        stripped="${entry%/}"
        campaign="${stripped##*/}"
        [[ "$campaign" =~ (22|23|24|25) ]] || continue
        printf '%s/%s/HWWNano/%s\n' "$BASE" "$user" "$campaign" >> "$output"
    done < "$hww_listing"
}

crawl_campaign() {
    local campaign="$1" id result

    id="$(hash_id "$campaign")"
    result="$STATE/results/${id}.txt"
    : > "$result"

    if ! crawl_tree "$campaign" "$result"; then
        rm -f "$result"
        touch "$STATE/failures/campaign.${id}"
        return 1
    fi

    LC_ALL=C sort -u "$result" -o "$result"
    (( VERBOSE < 2 )) || printf '[%s] completed: %s\n' "$(ts)" "$campaign" >&2
}

export -f \
    ts die require_uint validate_configuration double_backoff hash_id log_failure \
    eos_ls_capture eos_find_capture crawl_tree discover_user crawl_campaign
export BASE OUT EOS_BIN P RETRY BACKOFF0 VERBOSE FIND_NAME_REGEX STATE ERR

validate_configuration

printf '[%s] Discovering users with shallow EOS listing...\n' "$(ts)" >&2
if ! eos_ls_capture "$USERS_RAW" "$BASE"; then
    die "Could not list base directory: $BASE (see $ERR)"
fi

: > "$USERS"
while IFS= read -r entry; do
    entry="${entry%$'\r'}"
    [[ "$entry" == */ ]] || continue
    entry="${entry%/}"
    user="${entry##*/}"
    [[ -n "$user" ]] && printf '%s\n' "$user"
done < "$USERS_RAW" | LC_ALL=C sort -u > "$USERS"

n_users="$(wc -l < "$USERS")"
n_users="${n_users//[[:space:]]/}"
printf '[%s] Checking %s user directories with P=%s...\n' "$(ts)" "$n_users" "$P" >&2

if ! xargs -r -P "$P" -d $'\n' -I{} bash -c 'discover_user "$1"' _ "{}" < "$USERS"; then
    :
fi

if compgen -G "$STATE/failures/discovery.*" >/dev/null; then
    die "At least one user directory could not be inspected; no output written (see $ERR)"
fi

: > "$CAMPAIGNS"
while IFS= read -r -d '' file; do
    cat "$file" >> "$CAMPAIGNS"
done < <(find "$STATE/discovery" -type f -name 'campaigns.*.txt' -print0)
LC_ALL=C sort -u "$CAMPAIGNS" -o "$CAMPAIGNS"

n_campaigns="$(wc -l < "$CAMPAIGNS")"
n_campaigns="${n_campaigns//[[:space:]]/}"
(( n_campaigns > 0 )) || die "No matching 22/23/24/25 HWWNano campaigns found"

printf '[%s] Found %s campaigns; crawling with P=%s...\n' "$(ts)" "$n_campaigns" "$P" >&2
if ! xargs -r -P "$P" -d $'\n' -I{} bash -c 'crawl_campaign "$1"' _ "{}" < "$CAMPAIGNS"; then
    :
fi

if compgen -G "$STATE/failures/campaign.*" >/dev/null; then
    die "At least one campaign could not be crawled completely; no output written (see $ERR)"
fi

: > "$ALL"
while IFS= read -r -d '' file; do
    cat "$file" >> "$ALL"
done < <(find "$STATE/results" -type f -name '*.txt' -print0)
LC_ALL=C sort -u "$ALL" -o "$ALL"

: > "$NOM"
: > "$SYST"
awk -v nominal="$NOM" -v systematic="$SYST" '
    /(do|up)_suffix/ { print > systematic; next }
    { print > nominal }
' "$ALL"

{
    cat "$NOM"
    printf '\n'
    cat "$SYST"
} > "$FINAL"

mv -f "$FINAL" "$OUT"

n_nom="$(wc -l < "$NOM")"
n_syst="$(wc -l < "$SYST")"
n_nom="${n_nom//[[:space:]]/}"
n_syst="${n_syst//[[:space:]]/}"

printf '\nWrote: %s\n' "$OUT"
printf 'Campaigns: %s\n' "$n_campaigns"
printf 'Nominal: %s\n' "$n_nom"
printf 'Systematics: %s\n' "$n_syst"

if [[ -s "$ERR" ]]; then
    printf 'EOS retry/error log: %s\n' "$ERR"
else
    rm -f "$ERR"
fi
