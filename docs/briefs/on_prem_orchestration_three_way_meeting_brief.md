# On-Premises Agentic Workflow Orchestration
## Temporal vs. Restate vs. Camunda 8 — Meeting Brief & Technical Comparison

**Prepared:** October 15, 2026  
**Meeting:** October 16, 2026  
**Context:** Enterprise internal security/vulnerability dashboard; locked-down infrastructure; **no cloud-hosted orchestration**; event-driven and LLM-assisted processes; security-sensitive actions require **human review and authorization**.  
**Status:** Architecture research and provisional recommendation — **not a production certification, vendor quote, or measured benchmark**.

> **Current position:** **Temporal remains the default candidate for a shared, code-first enterprise orchestration backbone. Restate is the strongest developer-experience challenger. Camunda is the strongest option when managed human tasks and understandable process diagrams are first-class requirements.** Shortlist all three for the same proof of concept (POC), with on-prem deployment/security as non-negotiable gates.

---

# PART I — What to say in the meeting (read this first)

## 1. The 45-second explanation

> “We're not choosing an AI model. We're choosing the **reliable coordinator** behind our security dashboard. It starts workflows, remembers completed steps, handles retries, waits for human approval, and recovers from crashes. **Temporal** defines the workflow in code and dispatches execution through workers and task queues. **Restate** makes application service handlers durable, often with less orchestration-specific scaffolding. **Camunda** defines much of the process in BPMN diagrams, has workers or connectors perform technical work, and provides native human-task functionality. All three can be self-managed; the decision is mainly about **developer workflow, human-task requirements, operations, licensing, and security controls**, not whether they can run an AI agent.”

## 2. The real workflow we are trying to support

```text
              SECURITY EVENT / API / SCHEDULE
                           |
                           v
                START INVESTIGATION
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Asset DB     Threat Intel     SIEM Data
             |             |             |
             +-------------+-------------+
                           |
                           v
                 INTERNAL LLM / AGENT
                 analyzes, recommends
                           |
                           v
                  DETERMINISTIC POLICY
                           |
                           v
                  REVIEW IN DASHBOARD
                    (human approves?)
                    /              \
                   v                v
                APPROVE           REJECT
                   |                |
                   v                v
            Guarded executor    Record reason
                   |                |
                   v                |
              Verify result         |
                   +--------+-------+
                            |
                            v
                 AUDIT + DASHBOARD STATUS
```

**Non-negotiable design rule:** The LLM can **propose** an action; it must not grant itself permission to run high-impact remediation. The dashboard/backend validates the approver; a separate policy-controlled executor validates the *exact approved action* again before execution.

## 3. One-screen comparison

| Decision factor | **Temporal** | **Restate** | **Camunda 8 Self-Managed** |
|---|---|---|---|
| **Core mental model** | “Workflow code schedules tasks; workers execute them.” | “My service handler runs durably through Restate.” | “The BPMN process diagram is executable.” |
| **Where flow is defined** | Application code | Application code | BPMN model (+ code/expressions) |
| **Who executes API/LLM work** | Activity workers | Your service handlers / durable calls | Job workers or connectors |
| **How work is dispatched** | Workers **poll task queues** | Restate **invokes registered handlers** | Engine creates jobs; workers **activate jobs** |
| **Pause for human approval** | Workflow awaits Signal / Update | Workflow awaits durable promise/event | Native BPMN **User Task** |
| **Ready-made business task inbox** | No — build/integrate | No — build/integrate | **Yes — Tasklist**; can also use own dashboard |
| **Parallel branches** | Yes | Yes; use durable concurrency APIs | Yes; parallel gateways / jobs |
| **Scale to ~1,000 users** | Plausible; load-test | Plausible; load-test | Plausible; load-test |
| **Production hosting** | Own server + database + workers | Own Restate server/cluster + handler services | Own Camunda platform + workers/connectors |
| **Licensing headline** | Server **MIT** | Server **BSL 1.1**; internal production explicitly permitted under grant | **Enterprise license required for production** |
| **Why pick it** | Established, flexible shared engine | Streamlined code-first development; durable service state | Visible processes + native approval/task management |
| **Main trade-off** | More framework and operational concepts | Newer platform; specific replay/agent-SDK integration rules | BPMN/platform/paid-license overhead |

**Important:** “Less complex” here is a **qualitative developer/architecture assessment**, not a benchmark or guaranteed engineering-hour saving.

---

# PART II — How developers actually build with each

## 4. Side-by-side architectural picture

### Temporal — explicit workflow/worker separation

```text
 [Existing Dashboard / Backend] -- start / Signal / Update --> [Temporal Server]
                                                            | history + queues
                                                            v
                                                   [Task Queue(s)]
                                                            |
                                                        workers poll
                                                            |
                                               +------------+-----------+
                                               |                        |
                                         [Workflow code]          [Activity code]
                                         decides next step        calls LLM / APIs
                                               |                        |
                                               +---- results/history --+

                       [Temporal Server] --> [Persistent database]
```

**A worker is a deployed application process, not necessarily one server per workflow or task.** One worker process can register and execute multiple workflow and activity types. Workflow and Activity workers may be combined or split into separately scalable pools.

**Development steps:**
1. Define a **Workflow** in an approved SDK language (Python, TypeScript, Java, Go, etc.).
2. Implement **Activities** for side effects (internal model calls, SIEM queries, remediation APIs).
3. Register workflow types/activities in a **Worker** and assign a **Task Queue**.
4. Deploy a **Temporal Service** with supported persistence, security, backups, observability, and the workers.
5. Make the dashboard/backend start executions and send an authorized **Signal** or **Update** when a reviewer responds.
6. Test retries, idempotency, long-running workflow version changes, and recovery.

**Illustrative pseudocode (not copy/paste SDK code):**

```python
async def investigate(alert_id):
    evidence = await execute_activity(fetch_evidence, alert_id)
    proposal = await execute_activity(call_internal_llm, evidence)
    await wait_until(approval_received)       # via Signal / Update
    if decision == "approve":
        await execute_activity(remediate_safely, proposal)
```

**Why it feels more complex:** You deliberately separate **workflow decisions** from **side-effecting Activities**, register workers, manage task queues, and keep workflow replay/versioning safe. That structure is useful for many services and teams, but it is more to learn up front. Temporal server persistence/history enables recovery; the server does **not** execute your Python/TypeScript workflow itself.

**Advantages:** mature durable workflow model; clear operational boundaries; independently scalable worker pools; broad language support; sophisticated waits, timers, retries and branching.

**Costs:** more concepts and deployment pieces; persistent database; team-built task inbox and approval authorization; careful deterministic workflow code and deployment/version management.

**Good fit:** A **long-lived enterprise-wide backend orchestration foundation** under a custom dashboard.

### Restate — durable application services

```text
 [Existing Dashboard / Backend] --> [Restate Server / Cluster]
                                            | invocation router
                                            | durable journal + state
                                            v
                                     [Your HTTP service]
                                      durable handlers
                                     +--------------+
                                     | ctx.run(...) |
                                     | ctx.promise  |
                                     +--------------+
                                            |
                                     [Internal APIs/LLM]

               Restate stores execution progress; no Temporal-style
               workflow worker polling/task queue setup is required.
```

**Restate still runs your code in deployed services**: fewer explicit orchestration abstractions does **not** mean “no workers, no compute, or no infrastructure.” Its server invokes registered application handlers; you deploy and scale those handler processes.

**Development steps:**
1. Define a **Restate Service / Workflow** handler using the SDK.
2. Wrap nondeterministic/side-effecting operations in **durable calls** (for example `ctx.run(...)`).
3. Use a **durable promise/callback** to wait for an approval; expose an authorized handler/backend route to resolve it.
4. Serve the handler endpoint, **register its deployment** with Restate, and deploy the Restate server/cluster on approved infrastructure.
5. Scale application service instances; configure state keys, concurrency/flow limits, and monitor/recover failed invocations.
6. Test journal replay, SDK compatibility, versioning and external side-effect idempotency.

**Illustrative TypeScript-like pseudocode (not copy/paste SDK code):**

```ts
async function investigate(ctx, alertId) {
  const evidence = await ctx.run("fetch", () => fetchEvidence(alertId));
  const proposal = await ctx.run("analyze", () => callInternalLLM(evidence));
  const decision = await ctx.promise("approval"); // resolved externally
  if (decision === "approve") {
    await ctx.run("remediate", () => remediateSafely(proposal));
  }
}
```

**What is genuinely easier than Temporal?**
- Business logic is written as **ordinary service handlers with durability primitives**, rather than needing separate Workflow/Activity/Worker registrations and task-queue polling.
- `ctx.run()` journals a completed operation so recovery can reuse its recorded result; useful for **many small model/tool/API calls**.
- **Embedded state** and **Virtual Objects** help coordinate per-alert or per-session state without always designing an additional state store.
- A single server binary can simplify local setup; production **HA clusters still require** stateful operations, backups, and recovery planning.

**What is *not* automatically easier?** Integrating agent SDKs that hide their tool loop, reasoning about replay-safe async execution, upgrading active handlers, tuning concurrency, and passing enterprise security review. Wrapping a whole agent in one durable step is easiest but **loses fine-grained step recovery**.

**Advantages:** concise code-first model; durable service RPC/state; efficient small-step architecture; potentially smaller infrastructure footprint.

**Costs:** younger operational ecosystem; BSL legal review; custom approval inbox; extra care with agent SDK internals, durable concurrency and Virtual Object key design.

**Good fit:** A **developer-owned service layer** with many AI/tool operations where minimizing orchestration scaffolding matters.

### Camunda — executable business-process model plus code

```text
         [Camunda Modeler]
           BPMN (.bpmn)
               |
          deploy model
               v
       [Camunda 8 engine]
               |
       +-------+---------+
       |                 |
   Service Task       User Task
       |                 |
     job /             Tasklist or
    connector       dashboard via API
       |                 |
       v                 v
  [Job worker]       [Human approves]
  calls LLM/API          |
       +----------+------+
                  |
            BPMN advances
```

**The BPMN diagram is the *definition of the process*, not a replacement for implementing integrations.** Camunda also has workers, connectors, code, APIs and production infrastructure.

**Development steps:**
1. Draw the process in **Camunda Modeler** using BPMN events, service tasks, gateways, timers and **User Tasks**.
2. Attach each technical service task to a **job type** or an available connector.
3. Write/deploy **job workers** for custom internal API and AI calls; configure connectors where approved.
4. Deploy the `.bpmn` model to **Camunda Self-Managed**.
5. Use Camunda **Tasklist** for approvals, or query/complete user tasks from the existing dashboard through secured APIs.
6. Version the BPMN model and workers; monitor process instances and incidents; test authorization and recovery.

**Example process modeled in BPMN:**

```text
(Start) --> [Enrich] --> [AI Analyze] --> [User Approval]
                                            |
                                      <Approved?>
                                      /         \
                                    Yes          No
                                     |            |
                               [Remediate]    [Record Reject]
                                     |            |
                                     +------v-----+
                                           (End)
```

**Advantages:** easy to communicate a stable approval flow; native user tasks, assignment, forms/Tasklist; understandable handoffs between human and software tasks; process visibility.

**Costs:** BPMN learning and process-model lifecycle; you still implement custom integrations; complex/dynamic agent reasoning may not map cleanly to boxes and gateways; **Self-Managed production needs an Enterprise license**. Operational footprint depends on the exact edition/components, not simply “one BPMN editor.”

**Good fit:** Lots of **human approval, escalation, policy-governed processes**, especially if stakeholders want to inspect process definitions visually.

---

## 5. Development effort: what is actually built and maintained?

| Work item | Temporal | Restate | Camunda |
|---|---|---|---|
| Define the control flow | Workflow source code | Durable handler source code | BPMN model + expressions/optional code |
| Connect to internal LLM and security APIs | Activities + workers | `ctx.run`/service calls in handlers | Workers or connectors |
| Configure execution | Worker registrations + queues | Handler deployment registration | Deploy BPMN + job types/workers |
| Pause for approval | Signal/Update handler + durable wait | Promise/callback/shared handler | BPMN User Task |
| Human-facing inbox | Build in dashboard | Build in dashboard | Tasklist provided; integration if dashboard is mandatory |
| Define approver permissions | Our backend + engine service auth | Our backend + Restate endpoint auth | Camunda permissions **plus** our backend/policy controls |
| Change a process step | Update workflow/activities; plan replay compatibility | Update handler; plan journal/deployment compatibility | Update BPMN version and affected workers |
| Troubleshoot | Temporal UI/history + app logs | Restate UI/journal/traces + app logs | Operate/Tasklist + worker logs |
| Operate stateful platform | Server + persistence DB + workers | Restate stateful server/cluster + service deployments | Self-Managed engine/platform + workers/connectors |

### Relative complexity — not a measured ranking

| Type of complexity | Temporal | Restate | Camunda |
|---|---|---|---|
| **Learning the developer model** | More named concepts (Workflow, Activity, Worker, Task Queue, replay) | Fewer scaffolding concepts, but journaling/replay still matter | BPMN/process semantics **and** integration code |
| **Simple code-first workflow** | More explicit setup | Often most compact | Draw/configure a model first |
| **Human approval work queue** | Mostly custom application work | Mostly custom application work | Native platform feature |
| **Dynamic agent/tool logic** | Natural in supported code/Activities | Natural in handlers; agent SDK integration can be tricky | Often delegated to code/agent worker, not entirely represented as BPMN |
| **Production operations** | External DB and service roles | Integrated runtime, but HA/storage are real | Self-Managed platform; footprint depends on chosen components |

**Meeting phrasing:** **Restate may be simpler to write; Camunda may be simpler to explain and administer human reviews; Temporal may be easier to standardize around for a complex shared platform.** Those are hypotheses for a POC, not universal facts.

---

# PART III — Questions that surfaced in the deeper research

## 6. “Is Restate bad at parallelism?” — **No**

These are *three different* parallelism questions; avoid mixing them up.

**(A) Many users / separate workflow executions.** All three can process many independent executions concurrently. **1,000 users is not itself a meaningful engine benchmark**: what matters is *peak workflow starts, concurrent active work, operations per workflow, time awaiting approval, downstream LLM/API limits, and latency targets*.

**(B) Multiple independent operations inside one investigation.** All three can fetch SIEM, threat intel, and asset data concurrently:

```text
                    Investigation
                        |
               +--------+--------+
               |        |        |
             SIEM     Asset DB   Threat Intel
               |        |        |
               +--------+--------+
                        |
                  AI synthesis
```

- **Temporal:** schedule concurrent Activities and await the group through SDK-supported deterministic concurrency.
- **Restate:** start durable operations concurrently and combine them with **Restate concurrency primitives** (`RestatePromise.all()` in TypeScript; analogous SDK support elsewhere).
- **Camunda:** model parallel branches/gateways and execute service jobs concurrently with sufficient workers.

**(C) Third-party AI agent frameworks that manage their *own* async tool loop.** This is the real Restate caveat. Restate documents that fine-grained durable integrations should **not rely on native `Promise.all()` / `asyncio.gather()` to coordinate Restate-backed tool calls** because replay can observe a different completion order. Use Restate's durable concurrency primitives or an explicitly supported integration. It also notes constraints around streaming responses inside `ctx.run()` and propagating suspension/terminal errors.

**Temporal also needs deterministic workflow code** and does not allow arbitrary HTTP/LLM operations in workflow logic. The integration question is **which SDK's existing execution loop will require less adaptation** — not “which orchestrator has parallelism.”

## 7. “Can it grow from a dozen people to 1,000?” — **Potentially yes for all three**

**Illustrative numbers (not benchmarks):**

- **1,000 users × 5 starts/day = 5,000 workflow starts/day**, averaging ~0.17 starts/sec over an 8-hour working day. That may be modest orchestration load.
- **1,000 simultaneous starts × 5 AI operations = 5,000 AI operations** competing for resources in a burst. This could overwhelm the **internal LLM** even if orchestration is healthy.
- **1,000 pending approvals** is a different workload again: most are durably *waiting*, not burning CPU while blocked.

**How capacity is managed:**

| Dimension | Temporal | Restate | Camunda |
|---|---|---|---|
| Scale execution capacity | More activity/workflow worker processes; separate task queues | More handler-service instances + appropriately sized server cluster | More job workers + appropriately sized engine |
| Keep LLM from being overwhelmed | Worker concurrency / per-queue capacity + application limits | Durable invocation flow/concurrency controls + application limits | Worker/concurrency limits + application limits |
| Isolate workloads | Different task queues/worker pools | Separate handlers/services; keyed objects; flow-control scopes | Different job types/worker pools/process definitions |
| Main load question | Queue latency and workflow-task throughput | Invocation backlog and journal/server throughput | Job backlog and process engine throughput |

**Special Restate point: Virtual Objects.** A Virtual Object has a **single writer per object key** (while allowing concurrent readers). Properly keyed per alert or agent session, independent work proceeds concurrently. **A single global object key could serialize unrelated requests and become a bottleneck.** For multi-step approval lifecycles, prefer Restate's Workflow abstraction instead of one global exclusively locked object.

**Conclusion:** Do **not** eliminate Restate based on 1,000 users. Require POC testing with burst load, sustained load, and hundreds of approvals waiting.

## 8. “What is each platform actually persisting?”

- **Temporal:** Event History of workflow execution, including scheduled/completed Activities and received Signals/Updates. Worker replay reconstructs workflow state from history. Completed recorded Activities need not rerun merely to replay the workflow.
- **Restate:** Durable **journal** of handler operations and results; replay can reuse journaled steps. Some per-entity state can live in Restate's embedded KV store.
- **Camunda:** Process instances, BPMN position, variables, jobs, timers and user-task lifecycle managed by the process engine.

**All three** can recover after certain crashes. **None by itself guarantees an arbitrary external action ran exactly once.** A side effect can succeed just before a worker crashes, leaving the orchestrator unsure whether it happened. Use idempotency keys, compare-and-set/check-before-change APIs, and reconciliation.

## 9. “Does BPMN mean no code?” — **No**

The BPMN model specifies **what runs and when**. A service task may use a ready-made connector; a custom security API or LLM tool usually still requires configuration and/or a **job worker written in code**. Camunda's selling point is **process modeling plus first-class human tasks**, not eliminating developers.

## 10. “Which one has the best native approval support?”

**Camunda**, if the need is a ready-made **human task system**: a defined User Task, candidate/assignee information, Tasklist UI, and task APIs. **Temporal and Restate** can durably wait for a response but your team must typically implement the pending-approval queue, assignment rules, reminder/escalation behavior, and review UI.

**Security nuance:** On Camunda 8.9, Tasklist V2 uses an **authorization-based model** rather than the legacy Tasklist V1 user-task visibility restrictions; current docs describe task-level/property-based permissions, but applicability depends on **version, role configuration, API identity, and permission precedence**. Do not assume that an assignee field by itself guarantees who can read or complete a task. Verify actual enforcement against the chosen version. **Every candidate still needs backend policy checks and approver identity evidence.**

---

# PART IV — Decision, security, and next steps

## 11. Pros/cons summary — easiest way to defend each option

| Candidate | Strongest arguments **for** | Strongest arguments **against** |
|---|---|---|
| **Temporal** | Established code-first durable engine; flexible across teams/services; clear worker/queue isolation; MIT server; control over on-prem setup | More explicit engineering model; external DB and platform operations; native business approval inbox absent; deterministic replay/versioning learning curve |
| **Restate** | Compact durable handlers, embedded state, no separate worker-polling contract, fine-grained durable tool calls, on-prem single binary/cluster | Younger ecosystem; agent SDK integration/replay details; BSL license legal review; native business approval inbox absent; HA and security still need engineering |
| **Camunda** | Executable diagrams, native user tasks/Tasklist, clear business/approval governance, process inspection | Enterprise production license; BPMN skills and versioned models; custom worker code still needed; dynamic agent logic less naturally expressed entirely as diagrams |

### Recommendation **by strategic goal**

- **Shared, long-lived enterprise engine hidden behind our dashboard:** **Temporal** is the *provisional leader*.
- **App/service team that wants the smallest code-first durable workflow model:** **Restate** deserves a full head-to-head POC with Temporal.
- **A process platform where multiple teams need to model, inspect and perform human tasks:** **Camunda** becomes much more attractive, possibly the leader.

**Recommended meeting outcome:** Agree on the first concrete workflow, non-negotiable security gates, and **one standardized POC** for all three — **not** a final selection based on product demos.

## 12. Hard requirements before any scoring

| **Pass/fail gate** | What must be demonstrated |
|---|---|
| **Fully on-prem** | Control plane, data, credentials, SDK endpoint, model calls, logs and approval workflows run inside allowed infrastructure. Test with **internet egress denied**, including any activation/telemetry needs. |
| **Software/licensing approval** | Legal/procurement reviews exact server, UI, SDK, connectors and production/support terms. |
| **Identity + policy** | Internal IdP/SSO where required, service authentication, fine-grained **API-enforced** authorization, segregation of duties, maker-checker if needed. |
| **Human approval integrity** | Exact proposed action displayed and bound to the approval; reject, timeout, duplicate-click, stale decision and escalation paths defined. |
| **Recovery and safe retries** | Survive component restarts; avoid duplicate remediation with an idempotent action API; recover after failed model/API calls. |
| **Confidentiality + audit** | Control payload retention/redaction/encryption; export useful records to internal SIEM; use independent tamper-evident audit retention when required. |
| **Operations** | Supported HA deployment, backups/restores, upgrades, metrics, RTO/RPO, owner/on-call plan. |

**Caution:** An orchestrator's execution log is **not automatically a compliant, immutable audit record**, and a built-in task UI is **not automatically sufficient authorization** for regulated security actions.

## 13. POC: same workflow, same tests, same measurements

**Build once conceptually; implement three times:**

`Fake security event → concurrently query 3 internal mock APIs → run mock/internal LLM → policy check → create dashboard approval → approved/rejected branch → idempotent mock remediation → verify → audit.`

| Test | Evidence the team should collect |
|---|---|
| **Developer implementation** | Time to first end-to-end workflow; number of services/configuration files; code/diagram complexity; testability. |
| **Long approval** | Leave cases paused across worker and orchestrator restarts, new deployments, and multi-day intervals. |
| **Parallelism** | Three API calls actually overlap; correct results when completion order changes. |
| **100/1,000-workflow bursts** | Start latency, scheduling backlog, completions/sec, CPU/RAM/storage, errors, downstream saturation. |
| **Agent compatibility** | Existing/proposed agent SDK works with model calls, tool calls, parallel branches, suspension and failure handling. |
| **Partial failure** | Kill process after external action succeeds but before result is recorded; **no duplicate harmful effect**. |
| **Approval security** | Unauthorized user, self-approval, stale proposal, and duplicate/competing approvals all denied appropriately. |
| **Disconnected environment** | Egress-deny test including registration, UI access, authentication and operations. |
| **Day-two operations** | HA failover, backup/restore, upgrades with active workflows, monitoring, evidence export, support model. |

**Do not report a “winner” from a vendor throughput graphic.** Run the same tests with your internal model/API limits and approved hardware.

## 14. Questions worth asking the team tomorrow

**Most decision-changing questions** (in suggested priority order):

1. **What is the exact first production workflow?** Is it a fixed approval process or an AI agent with many dynamic tool steps?
2. **Is this one dashboard's backend or an enterprise-wide shared orchestration platform?** How many teams and languages will use it?
3. **Will approvers work only in our existing dashboard**, or is a separate native task inbox acceptable/desirable?
4. **What does “on-prem” mean in practice?** Physical data centre, private Kubernetes, isolated VMs, and absolutely zero public egress — including license checks?
5. **What is the planned agent SDK and language?** Custom Python, LangGraph, OpenAI Agents SDK, Semantic Kernel, TypeScript, etc. This materially changes Restate integration cost.
6. **What infrastructure is already approved?** PostgreSQL, Kubernetes, object storage, secrets vault, SIEM, IdP, monitoring, internal LLM serving.
7. **How many executions, not just users?** Peak starts/sec, simultaneous LLM calls, waiting approvals, average steps per case, backlog limits.
8. **Which controls are mandatory?** Dual approval, reviewer assignment, reapproval on proposal changes, escalation, audit retention, encryption, geographic restrictions.
9. **Who owns the platform in production?** SRE/on-call, patching, DR, support SLA, and acceptable commercial license cost.

## 15. Short responses to predictable questions

**“Why not just write Python and cron jobs?”** Ordinary scripts can do the work, but reliable recovery, wait-for-approval state, retry semantics, distributed coordination and execution visibility quickly become a custom orchestration platform.

**“Is Restate just a lighter Temporal?”** Not exactly. Both provide durable execution, but Temporal has explicit workflow/Activity workers and task queues; Restate uses durable application handlers plus an invocation/journal runtime. Different abstractions and trade-offs, not strictly a subset.

**“If Restate is easier, why not immediately choose it?”** Simpler handler code is valuable, but we still need evidence for agent SDK integration, enterprise authorization, HA/DR, operator familiarity, support, licensing and 1,000-user peak behavior.

**“Does Temporal require one worker per user or per activity?”** No. A deployed worker process can execute many tasks; concurrency is controlled and scaled with additional worker processes/instances.

**“Does Camunda eliminate custom workers?”** No. It can use connectors, but custom service tasks usually involve integration code and job workers.

**“Can we keep approval in our own dashboard?”** Yes with all three. Camunda has native user-task infrastructure; Temporal and Restate require more application-side task management. For every engine, the dashboard/backend must independently enforce reviewer permissions.

**“Does durable mean exactly-once remediation?”** No. Use guarded, idempotent external APIs. The orchestrator coordinates retries; it cannot erase uncertain outcomes in systems it does not control.

---

# Sources — official documentation (checked October 15, 2026)

**Temporal**
- [How Temporal Workers work](https://docs.temporal.io/workers)
- [Self-hosted guide and production checklist](https://docs.temporal.io/self-hosted-guide)
- [Workflow Signals, Queries and Updates](https://docs.temporal.io/encyclopedia/workflow-message-passing)
- [Production deployment](https://docs.temporal.io/production-deployment)
- [MIT server license](https://github.com/temporalio/temporal/blob/main/LICENSE)

**Restate**
- [Core architecture and durable execution](https://docs.restate.dev/foundations/key-concepts)
- [Basic Services, Virtual Objects and Workflows](https://docs.restate.dev/foundations/services)
- [Durable parallel/concurrent operations](https://docs.restate.dev/develop/ts/concurrent-tasks)
- [Agent framework integration caveats (parallelism, streaming, replay)](https://docs.restate.dev/ai/sdk-integrations/integration-guide)
- [Human-in-the-loop / pause and resume](https://docs.restate.dev/ai/patterns/human-in-the-loop)
- [Server BSL license and internal-use grant](https://github.com/restatedev/restate/blob/main/LICENSE)
- [Restate's own Temporal comparison (vendor perspective)](https://restate.dev/vs/temporal)

**Camunda**
- [BPMN service tasks and job workers](https://docs.camunda.io/docs/8.9/components/modeler/bpmn/service-tasks/)
- [BPMN user tasks and approvals](https://docs.camunda.io/docs/8.9/components/modeler/bpmn/user-tasks/)
- [Tasklist authorization — version-specific](https://docs.camunda.io/docs/8.9/components/tasklist/user-task-authorization/)
- [Orchestration cluster authorization and permissions](https://docs.camunda.io/docs/8.9/components/concepts/access-control/authorizations/)
- [Self-Managed deployment options](https://docs.camunda.io/docs/8.9/self-managed/deployment/)
- [Self-Managed production licensing](https://camunda.com/pricing/)

**Research notes:** Product claims are based mainly on vendor-maintained technical docs, cross-checked against license text where relevant; actual performance, disconnected operation, feature entitlements, and organizational compliance are **unverified until a deployment-specific POC and security/legal review**. Complexity comparisons are engineering judgments, not published objective scores.
