# Shared helpers for daily-work scripts. Sourced, not run.

TEMPLATES="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/templates"
SLUG_RE='^[a-z0-9-]+$'

refuse() { echo "refused: $*"; exit 1; }

# Usage telemetry (README "Telemetry"). Never fails and never waits for the network.
telemetry() { python3 "$(dirname "${BASH_SOURCE[0]}")/telemetry.py" "$@" 2>/dev/null || true; }

# Content logging (README "Content logging"). Does nothing when DAILY_WORK_CONTENT=0.
content() {
  [ "${DAILY_WORK_CONTENT:-}" = 0 ] && return 0
  python3 "$(dirname "${BASH_SOURCE[0]}")/content.py" "$@" 2>/dev/null || true
}

# Copy template $1 to $2, filling <project>, <slug>, <date>, <title>, <id> from env,
# and replacing the <description> placeholder line with env ASK.
fill() {
  mkdir -p "$(dirname "$2")"
  awk '
    function sub_all(s, tok, val,   i, out) {
      out = ""
      while ((i = index(s, tok)) > 0) { out = out substr(s, 1, i - 1) val; s = substr(s, i + length(tok)) }
      return out s
    }
    $0 == "<description>" { print ENVIRON["ASK"]; next }
    {
      s = sub_all($0, "<project>", ENVIRON["PROJECT"])
      s = sub_all(s, "<slug>", ENVIRON["SLUG"])
      s = sub_all(s, "<title>", ENVIRON["TITLE"])
      s = sub_all(s, "<id>", ENVIRON["ID"])
      print sub_all(s, "<date>", ENVIRON["DATE"])
    }' "$1" > "$2"
}

# Put line $3 at the end of the "## " section $2 of file $1, adding the section if missing.
add_under() {
  [ -f "$1" ] || : > "$1"
  H="$2" LINE="$3" awk '
    { L[NR] = $0 }
    END {
      h = ENVIRON["H"]; line = ENVIRON["LINE"]; s = 0
      for (i = 1; i <= NR; i++) if (L[i] == h) { s = i; break }
      if (!s) {
        for (i = 1; i <= NR; i++) print L[i]
        if (NR && L[NR] != "") print ""
        print h; print line; exit
      }
      last = s
      for (i = s + 1; i <= NR && L[i] !~ /^## /; i++) if (L[i] != "") last = i
      for (i = 1; i <= NR; i++) { print L[i]; if (i == last) print line }
    }' "$1" > "$1.tmp" && mv "$1.tmp" "$1"
}
