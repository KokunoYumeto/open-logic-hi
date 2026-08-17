$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot 'source\locale\hi'
$bibliography = Join-Path $repoRoot 'source\bib'
$output = Join-Path $repoRoot 'build\out'
New-Item -ItemType Directory -Force -Path $output | Out-Null
$oldBibInputs = $env:BIBINPUTS
$oldBstInputs = $env:BSTINPUTS
try {
    $env:BIBINPUTS = $bibliography + [IO.Path]::PathSeparator + $oldBibInputs
    $env:BSTINPUTS = $bibliography + [IO.Path]::PathSeparator + $oldBstInputs
    Push-Location -LiteralPath $source
    try {
        & latexmk -g -xelatex -interaction=nonstopmode -halt-on-error -file-line-error `
            ('-outdir=' + $output) 'open-logic-complete-hi-build.tex'
        if ($LASTEXITCODE -ne 0) { throw "latexmk failed with exit code $LASTEXITCODE" }
    } finally { Pop-Location }
} finally {
    $env:BIBINPUTS = $oldBibInputs
    $env:BSTINPUTS = $oldBstInputs
}
