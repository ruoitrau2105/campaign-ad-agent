# Phase 05 - AgentBase Cloud Deploy

## Status

Blocked on environment prerequisites.

## What Passed

The project is ready for AgentBase Custom Agent deployment from a code/runtime perspective:

- Container listens on `0.0.0.0:8080`.
- `GET /health` returns HTTP 200.
- `POST /invocations` exists for agent-style requests.
- `.dockerignore` excludes `.env`, `.greennode.json`, `.agentbase/`, local skills, contest material, and plans.
- Local gates pass:
  - `pytest -q`
  - `python evals\run.py`
  - `scripts\smoke_docker.ps1`

## Current Blockers

The actual AgentBase cloud deployment cannot proceed yet because the official AgentBase shell scripts reported:

| Check | Status | Required Fix |
| --- | --- | --- |
| IAM credentials | Missing | Configure `GREENNODE_CLIENT_ID` and `GREENNODE_CLIENT_SECRET`, or import `.greennode.json` using the official helper script. Do not paste secrets into chat. |
| `jq` | Missing | Install `jq` and ensure Git Bash can find it on `PATH`. |

The Git Bash path exists locally:

```text
C:\Program Files\Git\bin\bash.exe
```

## Preflight Command

Run:

```powershell
.\scripts\agentbase_preflight.ps1
```

Run with local gates:

```powershell
.\scripts\agentbase_preflight.ps1 -RunLocalGates
```

## Credential Setup Options

Use the official AgentBase helper scripts only. Do not read `.env` or `.greennode.json` manually.

Option 1: import from a credentials JSON file:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/save_iam_credentials.sh --from-file /path/to/credentials.json
```

Option 2: save an existing `client_id` and secret without putting the secret on the command line:

```powershell
'YOUR_CLIENT_SECRET' | & 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/save_iam_credentials.sh --client-id 'YOUR_CLIENT_ID' --secret-stdin
```

Then verify:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/check_credentials.sh iam
```

## Recommended Deploy Parameters

These are defaults to confirm before the mutating cloud deployment:

| Parameter | Recommended Value |
| --- | --- |
| Resource type | Custom Agent |
| Runtime name | `campaign-ad-agent` |
| Registry | AgentBase managed Container Registry |
| Network mode | `PUBLIC` |
| Build platform | `linux/amd64` |
| Flavor | `1x1-general` if available |
| Min replicas | `1` |
| Max replicas | `1` |
| CPU scale | `50` |
| Memory scale | `50` |
| Env file | `none` for mock mode, or an env file if enabling live MaaS |

## Deploy Sequence After Blockers Are Fixed

1. Verify IAM credentials:

   ```powershell
   & 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/check_credentials.sh iam
   ```

2. Fetch CR repo metadata:

   ```powershell
   & 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/cr.sh repo get
   ```

3. Login to AgentBase managed CR:

   ```powershell
   & 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/cr.sh credentials docker-login
   ```

4. Build and tag image using `{registryUrl}/{repoName}/campaign-ad-agent:{tag}` from CR metadata:

   ```powershell
   docker build --platform linux/amd64 -t <image-url> .
   ```

5. Push image:

   ```powershell
   docker push <image-url>
   ```

6. List runtime flavors and confirm `1x1-general` is available:

   ```powershell
   & 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/runtime.sh flavors
   ```

7. Create or update runtime with managed CR credentials:

   ```powershell
   & 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/runtime.sh create `
     --name campaign-ad-agent `
     --image <image-url> `
     --flavor 1x1-general `
     --min-replicas 1 `
     --max-replicas 1 `
     --cpu-scale 50 `
     --mem-scale 50 `
     --from-cr
   ```

8. List endpoints and test cloud health:

   ```powershell
   & 'C:\Program Files\Git\bin\bash.exe' .agents/skills/agentbase/scripts/runtime.sh endpoints list <runtime-id>
   curl.exe <endpoint-url>/health
   ```

## Acceptance Criteria

- [ ] `.\scripts\agentbase_preflight.ps1` passes.
- [ ] AgentBase CR repo metadata is available.
- [ ] Image is pushed to AgentBase managed CR.
- [ ] Runtime status is `ACTIVE`.
- [ ] DEFAULT endpoint health returns HTTP 200.
- [ ] `POST /invocations` works on the cloud endpoint.
- [ ] Runtime ID, endpoint URL, image URL, and tag are recorded in this file or a deploy log.
