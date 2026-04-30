#!/bin/bash

TEXFILE="$1"
OUTDIR="$2"

echo "Debug: texFile = '$TEXFILE'"
echo "Debug: outDir = '$OUTDIR'"

# Parameter validation
if [[ -z "$TEXFILE" ]]; then
    echo "Error: texFile parameter is empty"
    exit 1
fi

if [[ -z "$OUTDIR" ]]; then
    echo "Error: outDir parameter is empty"
    exit 1
fi

PDFNAME="$TEXFILE.pdf"
SRC="$OUTDIR/$PDFNAME"

# Extract the tex directory from the output directory path
TEXDIR="$(dirname "$OUTDIR")"

echo "Debug: texDir = '$TEXDIR'"

DST="$TEXDIR/$PDFNAME"

echo "Moving PDF from '$SRC' to '$DST'"

if [[ -f "$SRC" ]]; then
    mv "$SRC" "$DST"
    echo "Success: PDF moved to $DST"
    
    # Clean up the output folder
    echo "Cleaning up output folder: $OUTDIR"
    if [[ -d "$OUTDIR" ]]; then
        # Remove all files related to this specific build
        BASEFILENAME="$TEXFILE"
        FILES_TO_REMOVE=(
            "$BASEFILENAME.aux"
            "$BASEFILENAME.fdb_latexmk"
            "$BASEFILENAME.fls"
            "$BASEFILENAME.log"
            "$BASEFILENAME.synctex.gz"
            "$BASEFILENAME.out"
            "$BASEFILENAME.toc"
            "$BASEFILENAME.bbl"
            "$BASEFILENAME.blg"
        )
        
        for file in "${FILES_TO_REMOVE[@]}"; do
            FULLPATH="$OUTDIR/$file"
            if [[ -f "$FULLPATH" ]]; then
                rm -f "$FULLPATH"
                echo "Removed: $file"
            fi
        done
        
        # Remove the output directory if it's empty
        if [[ -z "$(ls -A "$OUTDIR" 2>/dev/null)" ]]; then
            rmdir "$OUTDIR"
            echo "Removed empty output directory"
        fi
    fi
else
    echo "Error: Source PDF not found at $SRC"
    exit 1
fi