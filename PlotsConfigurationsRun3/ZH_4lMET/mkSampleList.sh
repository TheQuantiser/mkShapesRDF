BASE="/eos/cms/store/group/phys_higgs/cmshww"
OUT="files_list.txt"

# Find all *__part0.root, split into nominal vs systematics, then concatenate.
find -L "$BASE" -type f -name '*__part0.root' -print \
  | LC_ALL=C sort -u \
  | awk '
      /(^|\/)(do_suffix|up_suffix)(\/|$)/ { syst[ns++]=$0; next }
      { nom[nn++]=$0 }
      END {
        for (i=0;i<nn;i++) print nom[i]
        print ""  # blank line separator (optional)
        for (i=0;i<ns;i++) print syst[i]
      }
    ' > "$OUT"

echo "Wrote: $OUT"
