param(
    [string]$ImageName = "campaign-ad-agent:test",
    [string]$ContainerName = "campaign-ad-agent-smoke",
    [int]$HostPort = 8081
)

$ErrorActionPreference = "Stop"

docker info *> $null
docker build --platform linux/amd64 -t $ImageName .

$existing = docker ps -aq -f "name=$ContainerName"
if ($existing) {
    docker rm -f $ContainerName *> $null
}

docker run -d -p "${HostPort}:8080" --name $ContainerName $ImageName *> $null

try {
    $healthy = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:$HostPort/health" -TimeoutSec 2
            if ($response.status -eq "healthy") {
                $healthy = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $healthy) {
        docker logs $ContainerName
        throw "Container did not become healthy on port $HostPort"
    }

    .\venv\Scripts\python.exe scripts\smoke_local.py --base-url "http://127.0.0.1:$HostPort"
} finally {
    docker rm -f $ContainerName *> $null
}
