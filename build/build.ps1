param(
  [Parameter(Mandatory = $true)]
  [string]$WorkingDirectory
)

$ErrorActionPreference = 'Stop'
$sourceCommit = '9620cc73f9c8e0ad003c514a5d3748f29611c4c0'
$repoRoot = Split-Path -Parent $PSScriptRoot
$overlay = Join-Path $repoRoot 'source\locale\hi'
$working = [System.IO.Path]::GetFullPath($WorkingDirectory)

if (Test-Path -LiteralPath $working) {
  throw "WorkingDirectory already exists; provide a new empty path: $working"
}

git clone https://github.com/OpenLogicProject/OpenLogic.git $working
if ($LASTEXITCODE -ne 0) { throw 'Upstream clone failed.' }
git -C $working checkout --detach $sourceCommit
if ($LASTEXITCODE -ne 0) { throw 'Frozen source checkout failed.' }

Copy-Item -LiteralPath $overlay -Destination (Join-Path $working 'locale') -Recurse

$wrapperDirectory = Join-Path $working 'locale\hi\content\sets-functions-relations\sets'
$buildDirectory = Join-Path $working 'build-hi-0011'
New-Item -ItemType Directory -Path $buildDirectory | Out-Null

$xelatexArgs = @(
  '-no-pdf',
  '-interaction=nonstopmode',
  '-halt-on-error',
  '-file-line-error',
  '-recorder',
  '-jobname=00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER',
  ('-output-directory=' + $buildDirectory),
  'open-logic-hindi-working-reader-through-0011.tex'
)

Push-Location $wrapperDirectory
try {
  xelatex @xelatexArgs
  if ($LASTEXITCODE -ne 0) { throw 'XeLaTeX pass 1 failed.' }
  xelatex @xelatexArgs
  if ($LASTEXITCODE -ne 0) { throw 'XeLaTeX pass 2 failed.' }
  $xdv = Join-Path $buildDirectory '00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER.xdv'
  $pdf = Join-Path $buildDirectory '00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER.pdf'
  xdvipdfmx -E -o $pdf $xdv
  if ($LASTEXITCODE -ne 0) { throw 'xdvipdfmx conversion failed.' }
  Get-FileHash -Algorithm SHA256 -LiteralPath $pdf
} finally {
  Pop-Location
}
