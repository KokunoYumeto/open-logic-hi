# Reproducible build

Requirements used for the accepted build:

- XeTeX/XeLaTeX (MiKTeX-XeTeX 4.18 was used)
- xdvipdfmx 20260404
- packages required by the pinned Open Logic source
- the pinned Noto Serif Devanagari OFL font included in the source ZIP

Obtain and freeze the upstream source:

```powershell
git clone https://github.com/OpenLogicProject/OpenLogic.git OpenLogic
Set-Location OpenLogic
git checkout --detach 9620cc73f9c8e0ad003c514a5d3748f29611c4c0
```

Copy the source ZIP's `overlay/locale/hi` directory into the checkout as
`locale/hi`. Then build from
`locale/hi/content/sets-functions-relations/sets`:

```powershell
$buildDir = Join-Path (Get-Location) 'build-hi-0011'
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null

$xelatexArgs = @(
  '-no-pdf', '-interaction=nonstopmode', '-halt-on-error',
  '-file-line-error', '-recorder',
  '-jobname=00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER',
  ('-output-directory=' + $buildDir),
  'open-logic-hindi-working-reader-through-0011.tex'
)
xelatex @xelatexArgs
xelatex @xelatexArgs

xdvipdfmx -E `
  -o (Join-Path $buildDir '00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER.pdf') `
  (Join-Path $buildDir '00_OpenLogic_hi-Deva-IN_CUMULATIVE_READER.xdv')
```

The accepted PDF has 17 pages, 212,719 bytes, and SHA-256
`BC7D4F6280D2E3DA427715B7CA2DF5335E8057AD0C0DCBCADEF8C18E27360468`.
An independent build may carry a different byte hash because TeX can embed
timestamps. It must still compile successfully and pass the text, font, and
every-page rendered checks described in the evidence ZIP.
