$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$manifest = Join-Path $repoRoot 'evidence\ARTIFACT_SHA256.tsv'

$rows = Get-ChildItem -LiteralPath $repoRoot -Recurse -File |
  Where-Object {
    -not $_.FullName.StartsWith((Join-Path $repoRoot '.git'), [System.StringComparison]::OrdinalIgnoreCase) -and
    $_.FullName -ne $manifest
  } |
  Sort-Object FullName |
  ForEach-Object {
    $relative = $_.FullName.Substring($repoRoot.Length + 1).Replace('\', '/')
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash
    "$relative`t$($_.Length)`t$hash"
  }

$content = (@("path`tbytes`tsha256") + $rows) -join "`n"
[System.IO.File]::WriteAllText($manifest, $content + "`n", [System.Text.UTF8Encoding]::new($false))

[pscustomobject]@{
  Manifest = $manifest
  Rows = $rows.Count
  Sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash
}
