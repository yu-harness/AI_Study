param(
    [ValidateSet("Canary", "Promote", "Rollback")]
    [string]$Action = "Canary",
    [string]$Model,
    [string]$Namespace = "default"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

if ($Action -ne "Rollback" -and [string]::IsNullOrWhiteSpace($Model)) {
    throw "-Model is required for Canary and Promote actions"
}

$canaryManifest = Join-Path (Split-Path $PSScriptRoot -Parent) "k8s/text2sql-canary.yaml"

if ($Action -eq "Canary") {
    kubectl -n $Namespace exec statefulset/ollama -- ollama pull $Model
    kubectl -n $Namespace apply -f $canaryManifest
    kubectl -n $Namespace annotate ingress/text2sql-api-canary --overwrite "nginx.ingress.kubernetes.io/canary-weight=10"
    kubectl -n $Namespace set env deployment/text2sql-api-canary "AGENT_MODEL=$Model"
    kubectl -n $Namespace rollout status deployment/text2sql-api-canary
    Write-Output "Canary model $Model is receiving 10% traffic."
    exit 0
}

$currentModel = kubectl -n $Namespace get deployment/text2sql-api -o "jsonpath={.spec.template.spec.containers[?(@.name=='api')].env[?(@.name=='AGENT_MODEL')].value}"
$historyText = kubectl -n $Namespace get deployment/text2sql-api -o "jsonpath={.metadata.annotations.text2sql\.ai/model-history}"
$history = @($historyText -split "," | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($history.Count -eq 0 -or $history[0] -ne $currentModel) {
    $history = @($currentModel) + @($history | Where-Object { $_ -ne $currentModel })
}

if ($Action -eq "Rollback") {
    if ($history.Count -lt 2) {
        throw "No previous model is available in deployment history"
    }
    $Model = $history[1]
}

kubectl -n $Namespace exec statefulset/ollama -- ollama pull $Model
$updatedHistory = @($Model, $currentModel) + @(
    $history | Where-Object { $_ -ne $Model -and $_ -ne $currentModel }
)
$updatedHistory = @($updatedHistory | Select-Object -Unique | Select-Object -First 3)
$historyAnnotation = $updatedHistory -join ","

kubectl -n $Namespace annotate deployment/text2sql-api --overwrite "text2sql.ai/model-history=$historyAnnotation"
kubectl -n $Namespace set env deployment/text2sql-api "AGENT_MODEL=$Model"
kubectl -n $Namespace rollout status deployment/text2sql-api
$canaryDeployment = kubectl -n $Namespace get deployment/text2sql-api-canary --ignore-not-found -o name
if ($canaryDeployment) {
    kubectl -n $Namespace annotate ingress/text2sql-api-canary --overwrite "nginx.ingress.kubernetes.io/canary-weight=0"
    kubectl -n $Namespace scale deployment/text2sql-api-canary --replicas=0
}

Write-Output "$Action completed. Active model: $Model. Retained history: $historyAnnotation"
