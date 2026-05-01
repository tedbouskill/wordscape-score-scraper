#!/bin/bash
# Usage: ./convert.sh <file>

file="$1"
ext="${file##*.}"
base="${file%.*}"

if [[ "$ext" == "tex" ]]; then
    # Look for a \bibliography{} directive
    bibfile=$(grep -oP '\\bibliography\{([^\}]*)\}' "$file" | sed -E 's/\\bibliography\{//;s/\}//')
    if [[ -n "$bibfile" && -f "$bibfile.bib" ]]; then
        pandoc "$file" --filter pandoc-citeproc --bibliography="$bibfile.bib" -s --shift-heading-level-by=1 -o "$base.md"
    else
        pandoc "$file" -s --shift-heading-level-by=1 -o "$base.md"
    fi
    echo "Converted $file to $base.md"
elif [[ "$ext" == "md" ]]; then
    pandoc "$file" -s -o "$base.tex"
    echo "Converted $file to $base.tex"
else
    echo "Unsupported file extension: $ext"
    exit 1
fi
