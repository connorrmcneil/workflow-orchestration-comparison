# Agentic Orchestration — Meeting One-Pager
**16 October 2026 | Enterprise security dashboard | Strict on-prem requirement**

## The recommendation
**POC three tools:** **Temporal (default favorite)**, **Camunda 8 Self-Managed (best approval-heavy alternative)**, and **Restate (lightweight developer-first challenger)**. **Do not** commit to an enterprise standard until an offline deployment, human-approval, failure-recovery, and security test passes.

## What the orchestrator does
Security finding → enrich → internal AI recommendation → deterministic policy → **pause for human approval in our dashboard** → authorized decision → idempotent action → verify → audit.

**It is the reliable coordinator, not the LLM.** The LLM recommends; the policy service and authorized human approve; the action API executes.

## Core tradeoffs

| Candidate | Why consider it | Biggest tradeoff |
|---|---|---|
| **Temporal** | Mature durable backend; SDKs across languages; strong long-lived workflow recovery; on-prem MIT server | We operate cluster/DB/workers; build approval inbox, strict auth and audit integration; deterministic replay rules |
| **Camunda 8** | BPMN diagrams, native human tasks/Tasklist, governed people + system + AI processes; self-managed | Production enterprise license; more BPMN/platform overhead; confirm task-level authorization on exact version |
| **Restate** | Smaller self-host runtime, durable calls, built-in state, polyglot SDKs | Newer ecosystem; **server BSL license** permits internal production but requires legal review |

## Other technologies — fast answers
**Inngest:** elegant event-driven functions; **self-host single-node labeled beta**, self-host support not guaranteed, **SSPL server**. **Trigger.dev:** excellent TS tasks; **self-host has no checkpoints/non-blocking waits**. **Workflow SDK:** excellent TS/app-embedded candidate; on-prem **Postgres World** exists, not necessarily enterprise shared platform. **Akka:** capable JVM agentic/distributed stack but larger architectural and licensing decision. **ZenML:** pipelines/artifacts. **Kitaru:** currently agent trace replay/evaluation; an older July comparison describes an earlier focus. **Prismatic:** **on-prem agent is connected to hosted Prismatic services**, not a fully self-hosted solution by default.

## 5 questions to resolve in the room
1. Do we need **a workflow engine inside our dashboard** or an **enterprise-wide business process + human-task platform**?
2. Must it run **with all outbound internet blocked**, including telemetry/activation/license calls? Is an internal IdP and internal LLM endpoint available?
3. Do we have **Kubernetes/VMs, PostgreSQL, HA/backups, and a team to run a stateful service**?
4. What exact approvals are needed: **reviewer assignment, maker/checker, SSO/RBAC, timeout/escalation, immutable evidence**?
5. Which **SDK languages**, throughput, workflow lifetime, SLA/RTO/RPO and procurement/licensing model are mandated?

## POC acceptance test
Run a fake vulnerability remediation across all 3 engines. Pause for approval, **kill/restart the worker**, send unauthorized and duplicate approvals, deploy a new version, resume, and simulate an action failing **after** its external side effect. Verify zero approval bypasses, safe idempotent retries, searchable audit evidence, and zero required public egress.

## Suggested 30-second presentation
> “Temporal currently looks like our strongest under-the-hood choice because we want a durable, on-prem engine behind our own security dashboard. I would not select it on reputation alone: Camunda is stronger where human tasks and visually governed business processes are central, while Restate may achieve the same application reliability with a simpler runtime. I'd propose testing those three against the exact same approval and crash-recovery workflow, and making our on-prem security requirements the first gate.”

**Reference:** `on_prem_agentic_orchestration_comparison.md` includes detailed product comparisons, deployment/license caveats, proposed architecture, and primary documentation links.
