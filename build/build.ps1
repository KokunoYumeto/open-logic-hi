$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$reader = Join-Path $repoRoot 'reader\00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER.pdf'
$content = Join-Path $repoRoot 'source\locale\hi\content'
$expectedReader = 'D08E9EA3D8398DB2A8F3CD3FC966A9849B41549A9282780EE1725B36B1716781'

if (-not (Test-Path -LiteralPath $reader)) {
  throw "Reader is missing: $reader"
}
$actualReader = (Get-FileHash -Algorithm SHA256 -LiteralPath $reader).Hash
if ($actualReader -ne $expectedReader) {
  throw "Reader SHA-256 mismatch: $actualReader"
}

$acceptedFiles = @(Get-ChildItem -LiteralPath $content -Recurse -File -Filter '*.tex')
if ($acceptedFiles.Count -ne 158) {
  throw "Expected 158 accepted content TeX files, found $($acceptedFiles.Count)"
}

[pscustomobject]@{
  Reader = $reader
  ReaderSha256 = $actualReader
  AcceptedTeXFiles = $acceptedFiles.Count
  Status = 'PASS'
}
