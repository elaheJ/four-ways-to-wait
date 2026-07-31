# Summarises the SMT measurement. Called by RUN-ME.bat; safe to run alone.
$ErrorActionPreference = "Stop"
$r = Join-Path $PSScriptRoot "results"

function Get-T2 ($file) {
    $p = Join-Path $r $file
    if (-not (Test-Path $p)) { return $null }
    $row = Import-Csv $p | Where-Object { [int]$_.threads -eq 2 }
    if (-not $row) { return $null }
    [pscustomobject]@{
        Time    = [double]$row.compute_s
        Speedup = [double]$row.compute_speedup
    }
}

Write-Host ""
Write-Host "--- SMT measurement -------------------------------------" -ForegroundColor Cyan
Write-Host ""

$ratios = @()
foreach ($run in 1..3) {
    $a = Get-T2 "smt_maskA_diffcores_run$run.csv"   # mask 5 : CPUs 0 and 2
    $b = Get-T2 "smt_maskB_samecore_run$run.csv"    # mask 3 : CPUs 0 and 1
    if ($null -eq $a -or $null -eq $b) { continue }

    $ratio = $b.Time / $a.Time
    $ratios += $ratio
    "  pass {0}:  maskA(0+2) {1,6:N3}s   maskB(0+1) {2,6:N3}s   ratio {3,5:N2}x" -f `
        $run, $a.Time, $b.Time, $ratio | Write-Host
}

if ($ratios.Count -eq 0) { Write-Host "  no data found"; exit }

$median = ($ratios | Sort-Object)[[int]([math]::Floor($ratios.Count / 2))]
Write-Host ""
"  median ratio: {0:N2}x" -f $median | Write-Host
Write-Host ""

# Which mask was slower? That one is the same-physical-core pairing.
$slowerIsB = $median -gt 1.0
if ([math]::Abs($median - 1.0) -lt 0.08) {
    Write-Host "  TOPOLOGY WARNING: the two masks performed almost identically." -ForegroundColor Yellow
    Write-Host "  Both may be hitting the same core pairing. Report this as-is;" -ForegroundColor Yellow
    Write-Host "  the mask labels may need re-deriving." -ForegroundColor Yellow
}
elseif (-not $slowerIsB) {
    Write-Host "  NOTE: maskA was the slower one, so the labels are swapped --" -ForegroundColor Yellow
    Write-Host "  CPUs 0 and 2 are SMT siblings on this machine, not 0 and 1." -ForegroundColor Yellow
    Write-Host "  The true SMT ratio is the reciprocal: {0:N2}x" -f (1 / $median) | Write-Host
}

$smt = if ($slowerIsB) { $median } else { 1 / $median }

Write-Host ""
Write-Host "--- Interpretation --------------------------------------" -ForegroundColor Cyan
Write-Host ""
"  Two threads sharing one core take {0:N2}x as long as two threads" -f $smt | Write-Host
Write-Host "  on separate cores."
Write-Host ""
if ($smt -ge 1.85) {
    Write-Host "  ~2.0x  ->  the second thread on a core bought essentially nothing."
    Write-Host "  This matches the Core Ultra's 1.93x, which has no SMT at all."
} else {
    $gain = [math]::Round((2.0 - $smt) / 2.0 * 100)
    "  Below 2.0x  ->  SMT is delivering. The second thread on a core" | Write-Host
    "  recovers about {0}% of what a whole extra core would have given." -f $gain | Write-Host
    Write-Host "  This is the treatment arm the paper was missing."
}
Write-Host ""

# Scaling sweep peaks
Write-Host "--- Scaling sweep ---------------------------------------" -ForegroundColor Cyan
Write-Host ""
foreach ($run in 1..3) {
    $p = Join-Path $r "scaling_run$run.csv"
    if (-not (Test-Path $p)) { continue }
    $rows = Import-Csv $p
    $best = $rows | Sort-Object { [double]$_.compute_speedup } -Descending | Select-Object -First 1
    "  pass {0}: peak compute speedup {1,5:N2}x at {2} threads" -f `
        $run, [double]$best.compute_speedup, $best.threads | Write-Host
}

# Per-core probe
Write-Host ""
Write-Host "--- Are the two cores identical? ------------------------" -ForegroundColor Cyan
Write-Host ""
foreach ($f in @("probe_cpu0.csv", "probe_cpu2.csv")) {
    $p = Join-Path $r $f
    if (Test-Path $p) { "  {0,-16} {1}" -f $f, (Get-Content $p -Raw).Trim() | Write-Host }
}
Write-Host ""
Write-Host "  These should agree closely -- this chip is homogeneous,"
Write-Host "  unlike the M1 (4P+4E) and the Core Ultra (8P+12E)."
Write-Host ""
