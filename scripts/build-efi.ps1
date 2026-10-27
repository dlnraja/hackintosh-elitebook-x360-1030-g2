# Download the pinned OpenCore and kext releases and assemble dist/EFI.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-Command "iasl")) {
    Write-Error "iasl is required. Install the ACPICA tools and make sure iasl is on PATH."
}

$Python = $null
foreach ($Candidate in @("python3", "python")) {
    if (Test-Command $Candidate) {
        $Python = $Candidate
        break
    }
}
if (-not $Python) {
    Write-Error "Python 3 is required."
}

& $Python "scripts/efi_build.py" "build" @args
exit $LASTEXITCODE
