param([int]$MutexTimeoutSeconds = 45, [ValidateSet('full','supplement')][string]$Mode='full')
$ErrorActionPreference = 'Stop'
$lane = Split-Path -Parent $PSScriptRoot
$source = Join-Path $lane 'source\locale\hi'
$bib = Join-Path $lane 'source\bib'
$output = Join-Path $lane 'build\replay'
$qa = Join-Path $lane 'qa\replay'
New-Item -ItemType Directory -Path $qa -Force | Out-Null
$driver = 'open-logic-complete-hi-reconciled.tex'
if($Mode -eq 'supplement'){$driver='open-logic-hi-supplement-diagnostic.tex';$output=Join-Path $output 'supplement-diagnostic'}
$job=[IO.Path]::GetFileNameWithoutExtension($driver)
New-Item -ItemType Directory -Path $output -Force | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$receipt = [ordered]@{schema='hindi-tex-mutex-build/v1';started_utc=$stamp;mutex='Global\InterlanguageTeXSlotV1';acquired=$false;abandoned=$false;driver=$driver;mode=$Mode;status='STARTING'}
$mutex = [Threading.Mutex]::new($false, 'Global\InterlanguageTeXSlotV1')
$acquired = $false
$previousBib = $env:BIBINPUTS
$previousBst = $env:BSTINPUTS
$process = $null
try {
    try {$acquired = $mutex.WaitOne([TimeSpan]::FromSeconds($MutexTimeoutSeconds))}
    catch [Threading.AbandonedMutexException] {$acquired=$true;$receipt.abandoned=$true}
    if(-not $acquired){throw 'Global TeX slot acquisition timed out; no engine launched.'}
    $receipt.acquired=$true
    $env:BIBINPUTS=$bib+[IO.Path]::PathSeparator+$previousBib
    $env:BSTINPUTS=$bib+[IO.Path]::PathSeparator+$previousBst
    $latexmk=(Get-Command latexmk -ErrorAction Stop).Source
    $arguments=@('-xelatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','-recorder',('-outdir="'+$output+'"'),$driver)
    $console=Join-Path $output ('latexmk-'+$stamp+'.stdout.log')
    $stderr=Join-Path $output ('latexmk-'+$stamp+'.stderr.log')
    # latexmk synchronously owns its engine/BibTeX/converter children. Keep the
    # mutex through its complete lifetime and immediate post-run log inspection.
    $process=Start-Process -FilePath $latexmk -ArgumentList $arguments -WorkingDirectory $source -WindowStyle Hidden -PassThru -RedirectStandardOutput $console -RedirectStandardError $stderr
    $receipt.pid=$process.Id
    $process.WaitForExit()
    $receipt.exit_code=$process.ExitCode
    $receipt.console_log=$console
    $receipt.stderr_log=$stderr
    $log=Join-Path $output ($job+'.log')
    if(Test-Path -LiteralPath $log){
        $receipt.log_sha256=(Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash
        $receipt.hard_log_lines=@(Select-String -LiteralPath $log -Pattern 'Undefined control sequence|LaTeX Error|Emergency stop|Fatal error|Missing character:|Missing \$ inserted|Extra \}|Runaway argument|^!|\.tex:\d+: '|ForEach-Object Line)
    }
    $pdf=Join-Path $output ($job+'.pdf')
    if(Test-Path -LiteralPath $pdf){$receipt.pdf_sha256=(Get-FileHash -LiteralPath $pdf -Algorithm SHA256).Hash;$receipt.pdf_bytes=(Get-Item -LiteralPath $pdf).Length}
    $receipt.status=if($process.ExitCode -eq 0){'BUILD_FINISHED_REQUIRES_ACCEPTANCE'}else{'BUILD_FAILED_REPAIR_REQUIRED'}
}
catch {$receipt.status='OPERATION_FAILED';$receipt.error=$_.Exception.Message}
finally {
    if($null -ne $process -and -not $process.HasExited){$process.WaitForExit()}
    $env:BIBINPUTS=$previousBib;$env:BSTINPUTS=$previousBst
    if($acquired){$mutex.ReleaseMutex()}
    $mutex.Dispose()
    $receipt.finished_utc=(Get-Date).ToUniversalTime().ToString('o')
    $receiptPath=Join-Path $qa ('BUILD-'+$stamp+'.json')
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
    $receipt | ConvertTo-Json -Depth 6
}
if($receipt.status -ne 'BUILD_FINISHED_REQUIRES_ACCEPTANCE'){exit 1}
