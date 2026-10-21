$ErrorActionPreference = "Stop"

$packageDirectory = Join-Path $PSScriptRoot "lambda-package"
$sourceDirectory = Join-Path $PSScriptRoot "..\src\flashcardApp"
$requirementsFile = Join-Path $PSScriptRoot "lambda-requirements.txt"

if (Test-Path -LiteralPath $packageDirectory) {
    Remove-Item -LiteralPath $packageDirectory -Recurse -Force
}
New-Item -ItemType Directory -Path $packageDirectory | Out-Null

python -m pip install --disable-pip-version-check --target $packageDirectory -r $requirementsFile
if ($LASTEXITCODE -ne 0) {
    throw "Could not install Lambda package dependencies."
}

Copy-Item -Path (Join-Path $sourceDirectory "*.py") -Destination $packageDirectory
