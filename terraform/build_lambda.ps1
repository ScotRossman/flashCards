$ErrorActionPreference = "Stop"

python (Join-Path $PSScriptRoot "build_lambda.py")
if ($LASTEXITCODE -ne 0) {
    throw "Could not build the Lambda deployment package."
}
