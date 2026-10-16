# On-Premises Agentic Workflow Orchestration — Technology Comparison

**Decision brief | 15 October 2026 | Internal engineering discussion**  
**Use case:** A regulated enterprise's internal security/vulnerability dashboard. Work can be triggered by security events, schedules, API calls, or AI analysis; some actions must pause for a human to review and approve before execution.

> **Bottom line:** **Shortlist Temporal, Camunda 8 Self-Managed, and Restate.** Start with **Temporal as the default technical proof of concept**, but **choose Camunda if built-in human-task management, process visibility, and business-owned workflow modeling dominate**. **Restate** is the strongest lean, developer-oriented alternative worth benchmarking against Temporal. None should be selected without an on-prem security and failure-recovery proof of concept.

**Confidence:** Architecture/feature descriptions are based principally on official documentation linked below. Fit judgments are analytical, **not lab-verified**. Exact licensing, support, disconnected operation, and governance controls require procurement/security review.

---

## 1. The 60-second explanation

A **workflow orchestrator** is the *reliable conductor*, not the AI model. It remembers which steps finished, retries failures safely, waits for events or approvals, and resumes after a process or machine restarts.

Example: `Vulnerability finding → fetch context → optional internal LLM analysis → policy check → create approval item → authorized employee approves → execute a guarded remediation → verify → retain evidence`.

**Three things often conflated:**

1. **Durable workflow engine:** Executes/retries/pauses/resumes a business process (Temporal, Restate, Inngest, Trigger.dev, Workflow SDK).
2. **Business process / human-task platform:** Models cross-team processes and assigns approval tasks (Camunda is strongest here).
3. **Agent framework / AI-evaluation tooling:** Makes model/tool decisions or tests agents. This is **complementary**, not automatically a substitute for a durable enterprise control plane (e.g., LangGraph, ZenML/Kitaru).

**On-prem vocabulary matters:** “Self-hosted engine,” “private cloud,” “bring your own cloud,” and “on-prem agent” are **not synonyms**. An acceptable solution must keep its **control plane, execution, state, credentials, logs/traces, and model access** inside approved infrastructure, with no required third-party calls. Prove this under a network egress-deny policy.

---

## 2. Side-by-side comparison — meeting view

**Legend:** ✅ documented self-hosted option; ⚠️ conditional / notable restrictions; ❌ fails the stated strict no-cloud gate as normally offered. **HITL** = human in the loop. “Built-in HITL” means a usable task inbox, not merely the ability to wait for a message.

| Technology | What it is | Full on-prem path? | Approval / HITL approach | Main attraction | Main concern for us | Verdict |
|---|---|---|---|---|---|---|
| **Temporal** | Durable code-first workflow engine | ✅ OSS engine + own workers | Durable Signals/Updates; **we build dashboard approval inbox / authorization** | Mature recovery model, broad SDKs, control | More infra + deterministic workflow rules | **#1 POC** |
| **Camunda 8** | BPMN process orchestration + human tasks | ✅ Self-Managed; **enterprise license in production** | **Native user tasks / Tasklist**, can also use our own UI | Explicit governance, ownership, visual approvals | License + platform/BPMN complexity; check per-task permissions by version | **#2 / #1 if approvals dominate** |
| **Restate** | Durable application handlers, workflows, RPC, state | ✅ self-hosted server/cluster | Durable promises/events; **we build inbox** | Lower ops footprint, fine-grained durable steps, polyglot | Smaller ecosystem; verify operations/security and BSL terms | **#3 / main challenger** |
| **Inngest** | Event-driven durable functions | ⚠️ self-hosted, but validate production mode/support | `waitForEvent` / events; **we build inbox** | Simple event + step API; limits and rate controls | Self-host single-node labeled beta; self-host support + SSPL review | **Conditional POC** |
| **Trigger.dev** | Background jobs and agent tasks | ⚠️ self-hosted Docker/K8s; cloud features differ | Waits / typed input; **we build inbox** | Great TypeScript DX, task monitoring | **Self-host lacks checkpoints / non-blocking waits**; TS-centric | **Not first choice for long approval waits** |
| **Workflow SDK (Vercel OSS)** | App-embedded durable TypeScript workflows | ✅ with **Postgres World** | Hooks/webhooks; **we build inbox** | Few concepts; fits a TS-first existing app | Newer ecosystem; smaller platform/governance surface | **App-level option, not default shared backbone** |
| **Akka** | JVM-based distributed/agentic application platform | ✅ documented self-managed path; commercial terms | Developer-built workflow / agent handling | Powerful event-driven actor/stateful system | Bigger architectural commitment; BSL/commercial production licensing | **Only if JVM/Akka architecture is strategic** |
| **ZenML** | MLOps / LLM pipeline orchestration | ✅ OSS/self-hosted | Not primarily a security approval inbox | ML pipelines, artifact lineage, reproducibility | Wrong primary abstraction for transactional dashboard workflows | **Complementary** |
| **Kitaru (ZenML team)** | Agent traces, replay & evaluation platform **currently** | ✅ OSS self-hosted | Not a general workflow approval replacement | Regression tests/evals for AI decisions | Older July comparison describes an earlier durable-agent focus; product has evolved | **Complementary** |
| **Prismatic** | Embedded integration platform (iPaaS) | ❌ typical **on-prem agent connects to Prismatic-hosted services** | Integration workflows, not our core approval plane | Many integrations for B2B SaaS products | On-prem connector ≠ fully on-prem orchestrator | **Exclude unless vendor proves true private deployment** |

**Important feature parity traps:** The *cloud* capabilities advertised by a vendor are not necessarily present in its *self-hosted* product. Compare the **exact product edition and deployment architecture**, not marketing homepages.

---

## 3. The three strongest candidates, explained

### A. Temporal — recommended baseline

**How it works:** Our application starts a **Workflow**. Temporal records a persistent **Event History**. **Workers** on our infrastructure poll **Task Queues** and execute workflow code and **Activities** (side-effecting jobs such as API calls and LLM inference). After interruption, workflow code replays against recorded history to restore progress; completed activity results do not need to be reexecuted as part of normal replay.

- **Best at:** Multi-step workflows crossing services and languages; retries, timeouts, parallel branches, long waits, scheduled jobs, crash recovery, and precise execution history.
- **On-prem:** MIT-licensed server; production requires a properly operated Temporal Service, persistence database, worker deployments, security, monitoring, backups, and upgrade strategy. Advanced visibility can use supported SQL stores; Elasticsearch/OpenSearch is **not universally required**.
- **Human approval:** Workflow waits durably. The dashboard exposes its own *pending action* and sends a **Signal** (asynchronous) or **Update** (validated, response-producing) after server-side permission checks. Temporal's Web UI is **not** the business approval inbox.
- **AI fit:** Invoke approved internal models as **Activities**, not inside deterministic workflow logic. LLM outputs can vary; isolate non-deterministic calls. Agents may reason dynamically, but permission checks remain deterministic and external to the model.
- **Pros:** Strong general-purpose backbone; mature SDK coverage; self-host path; vendor-neutral application languages; resilient waits; granular operational control.
- **Cons:** Workflow/Activity/Worker concepts and safe workflow versioning impose learning cost; production HA and persistence operations are nontrivial; self-hosted authN/authZ, auditing, encryption, and dashboard integration must be engineered rather than assumed.
- **Security caveat:** **Temporal Web UI login is not Temporal Service authorization.** Configure and test service-side ClaimMapper/Authorizer, network policy, mTLS and payload handling. Workflow event history aids reconstruction but is **not automatically a compliant immutable audit ledger**.

**Best fit when:** The company wants a durable **under-the-hood engine behind its own dashboard**, expects multiple application teams and languages, and can operate a stateful backend.

**Read:** [Self-hosted guide](https://docs.temporal.io/self-hosted-guide) · [Production components](https://docs.temporal.io/production-deployment) · [Signals, Queries and Updates](https://docs.temporal.io/encyclopedia/workflow-message-passing) · [Approval pattern](https://docs.temporal.io/design-patterns/approval) · [Self-host security](https://docs.temporal.io/production-deployment/self-hosted-guide/security) · [MIT license](https://github.com/temporalio/temporal/blob/main/LICENSE)

### B. Camunda 8 Self-Managed — strongest human-task/process alternative

**How it works:** Engineers and process owners describe a workflow using **BPMN** (boxes, branches, timers, gateways). **Zeebe** runs it; service workers execute integrations/agent calls. **User tasks** are explicit first-class workflow steps. **Tasklist** provides a human work queue, and Camunda APIs can back our custom dashboard instead.

- **Best at:** Approval-heavy flows, handoffs among teams, policy/process transparency, escalation, audit-oriented process reporting, and BPMN/DMN-based rules.
- **On-prem:** Available as Self-Managed. **Current production deployment requires a paid Enterprise license**; free local/non-production use is not the same as free enterprise production.
- **Human approval:** Native user tasks, assignment/completion, forms and due dates. More comes ready-made than with Temporal, but our dashboard would still need a custom integration if it is the system people should use.
- **AI fit:** Service/agent tasks may call internal model endpoints and human tasks gate risky actions. A graph for an approval policy is easier to show in a review meeting than arbitrary code.
- **Pros:** Business-readable diagrams; first-class user tasks; process monitoring; strong explicit separation of people, systems and AI.
- **Cons:** Subscription/procurement; heavier operational footprint; extra BPMN skills; integration and embedded approval UI still take work; possible overkill if the main goal is simple background jobs.
- **Security caveat — version-specific:** Camunda 8.8 Tasklist V2 defaults to **process-definition-level** access and its docs state **per-task visibility restrictions are not supported** in that mode. Version 8.9 adds task-oriented authorization guidance. **Test exact target version, API identity propagation, assignee restrictions, and authorization of *completion***—do not equate UI visibility with a secure approval policy.

**Best fit when:** The organization wants to standardize complex **human + automated + AI** business processes, needs a ready-made approval system, and accepts enterprise licensing.

**Read:** [Self-Managed pricing/licensing](https://camunda.com/pricing/) · [Camunda 8 licensing](https://github.com/camunda/camunda-docs/blob/main/docs/reference/licenses.md) · [Human-task quickstart](https://docs.camunda.io/docs/8.8/guides/orchestrate-human-tasks/) · [Task application architecture](https://docs.camunda.io/docs/8.8/apis-tools/frontend-development/task-applications/task-application-architecture/) · [8.8 Tasklist authorization caveat](https://docs.camunda.io/docs/8.8/components/tasklist/api-versions/)

### C. Restate — lean alternative that could beat Temporal on developer/ops fit

**How it works:** Restate persists the progress of **durable handlers**. An application exposes HTTP-invoked handlers; durable steps journal results to a **Restate server**. Restate also has workflows, durable RPC, and **Virtual Objects** (state and per-key concurrency), so the same runtime can coordinate service calls and manage per-entity state.

- **Best at:** Low-latency, event-heavy application orchestration; many small durable steps; stateful agents, services, and workflows with minimal separate worker-polling machinery.
- **On-prem:** Self-host the server as a single binary for development, or run replicated production clusters with persistent storage / snapshots. Application handlers still run in our infrastructure.
- **Human approval:** Build an approval endpoint / work queue and resume through persisted events, state, or durable promises. No Camunda-style business task inbox included by default.
- **AI fit:** Granularly journal individual model/tool operations and retries; useful when agents make many small calls or need per-object coordination.
- **Pros:** Lower infrastructure surface than Temporal; application-first handlers; several language SDKs; first-class durable state/communication.
- **Cons:** Smaller/younger ecosystem relative to Temporal; governance/admin operational practices require closer validation; per-step journaling and failure behaviors need testing for the actual workload.
- **License caveat:** The **server repo is BSL 1.1, not OSI open source** as of review. Its explicit additional-use grant **permits internal enterprise production deployments** but restricts offering a public Restate platform service. Legal must review exact license and intended usage. “Free internal use” does not mean “MIT/Apache licensed.”

**Best fit when:** The team wants durable execution and high-throughput service coordination **without** Temporal's larger cluster topology and is comfortable validating a newer runtime.

**Read:** [Restate overview](https://docs.restate.dev/) · [Official comparison](https://restate.dev/vs/temporal) · [Self-host deployment guides](https://docs.restate.dev/guides/) · [Server license](https://github.com/restatedev/restate/blob/main/LICENSE)

---

## 4. Remaining options — why they do or do not advance

| Product | Strength | What to verify or why not first choice | Official evidence |
|---|---|---|---|
| **Inngest** | Clean `event → durable function → step` design; waits, cron, built-in flow-control options; integrates into HTTP apps. | Official self-host docs acknowledge `inngest start` **single-node mode is labeled beta**, with persistence/metrics/retention hardening and **no guaranteed direct self-host support**. Server uses **SSPL + delayed Apache publication**, whereas SDKs use Apache 2.0. Validate HA, feature parity, security and legal use **before** advancing. “No workers” means no *Temporal-style polling workers*; our function-serving app still runs. | [Self-host guide](https://www.inngest.com/docs/platform-and-operations/self-host-inngest) · [Server license](https://github.com/inngest/inngest) |
| **Trigger.dev** | Smooth TypeScript task authoring, scheduling, realtime status, OpenTelemetry, managed execution options. | Self-hosted docs explicitly say **no checkpoints / non-blocking waits**, **no built-in autoscaling**, and no dedicated self-host support; evaluate resource cost and state durability during **days-long approval pauses**. Cloud marketing claims cannot be carried over unqualified. Also **TS-centric**. | [Self-host feature matrix](https://trigger.dev/docs/self-hosting/overview) · [Enterprise FAQ](https://trigger.dev/enterprise) |
| **Workflow SDK** | Open-source, TS-first durable execution; native stream/hook patterns; **Postgres World** supports self-hosted Docker/K8s/VM setups using PostgreSQL + graphile-worker. | Promising for a **single TS product/team**, but currently less compelling as a regulated enterprise-wide polyglot orchestration standard; ensure Postgres World's actual retention, RBAC, observability and incident response capabilities. Its “no infra” pitch is primarily for Vercel—**self-hosting still operates DB and processes**. | [Postgres World](https://workflow-sdk.dev/worlds/postgres) · [Temporal comparison](https://workflow-sdk.dev/docs/comparisons/workflow-sdk-vs-temporal) |
| **Akka** | Self-managed JVM distributed state/event-sourcing, streaming, workflows and agent capabilities; excellent option for an Akka/Java/Scala-oriented platform. | Not a drop-in Temporal replacement: adopting it makes a larger application architecture decision. **BSL / enterprise production-license review** required; check whether required persistence, AI controls and support run fully disconnected. | [Self-managed operations](https://doc.akka.io/operations/configuring.html) · [License FAQ](https://akka.io/bsl-license-faq) · [JVM integrations](https://doc.akka.io/sdk/integrations/index.html) |
| **ZenML** | Pipeline management, ML/LLM reproducibility and artifact lineage. | Useful if the project also builds/trains/evaluates models or pipelines, **not** the primary source of truth for day-to-day vulnerability-remediation approvals. | [ZenML overview](https://github.com/zenml-io/zenml/blob/main/docs/book/introduction.md) |
| **Kitaru** | Self-hosted capture/import of agent traces, replay-based evals/regression testing. | **Source freshness trap:** the linked **July 7, 2026** comparison presents Kitaru as a durable Python agent runtime. Its **current repo and ZenML docs focus on trace replay/evaluations**. Assess current software, not the earlier positioning; use to test AI behavior alongside a workflow engine. | [Current Kitaru repo](https://github.com/zenml-io/kitaru) · [ZenML product split](https://github.com/zenml-io/zenml/blob/main/docs/book/introduction.md) · [Older comparison](https://www.zenml.io/blog/inngest-vs-temporal) |
| **Prismatic** | B2B SaaS integrations and connectors to customer systems. | **Disqualifying under strict no-cloud:** its **on-prem agent** makes an mTLS connection **to services running in the Prismatic platform**, requiring outbound connectivity; the orchestration/control plane does not simply move on-prem because an agent does. A vendor-demonstrated fully private/self-managed offering would need separate assessment. | [On-prem agent architecture](https://prismatic.io/docs/integrations/connections/on-prem-agent/) |

---

## 5. Recommended architecture for our security dashboard

```text
Existing security findings / schedules / APIs / analyst requests
                           |
                           v
                 [Internal ingestion API]
                           |
                           v
              [Durable workflow orchestrator]
                           |
          +----------------+-------------------+
          |                |                   |
    [Enrich context] [Internal AI endpoint] [Deterministic policy/rules]
          |                |                   |
          +----------------+-------------------+
                           |
                 [Pending approval record]
                           |
                [Dashboard action queue]
                           |
     [Corporate SSO + RBAC + approver policy enforcement]
                           |
                  Approve / Reject / Escalate
                           |
                  [Workflow is resumed]
                           |
              [Guarded, idempotent action API]
                           |
                 [Verify actual outcome]
                           |
       [Central audit/evidence store + SIEM + monitoring]
```

**Separation of responsibilities:**

- **Orchestrator:** run state, timers, retries, transitions, compensation, correlation IDs.
- **AI service:** summarize and recommend (local/approved inference only); **never independently grant itself permission** to remediate.
- **Dashboard + backend:** present actionable review items; authenticate the employee; enforce user/group permissions, maker-checker / separation of duties, and decision reason.
- **Policy/command API:** checks scope and current policy again immediately before execution, even when an approval was previously granted.
- **Evidence system:** record event, model/prompt/policy version, immutable IDs, material inputs/outputs or hashes, proposed action, approver, timestamps, decision, attempted execution and verification outcome. Put durable **tamper-evident/WORM** retention in a separate governed system if compliance requires it.

**Critical reliability rule:** Durable execution does **not** make an arbitrary external API call execute *exactly once*. Activities/handlers may retry after partial failure. Use **idempotency keys**, conditional updates and reconciliation. Prevent duplicate remediation, tickets, access changes, or notifications.

**Do not persist secrets, full sensitive payloads, raw prompt bodies, or vulnerability details indiscriminately in engine history/traces**; use encrypted references and deliberate retention/redaction. Test authorization in the backend, not solely in the browser.

---

## 6. Selection criteria — hard gates before performance scoring

Treat these as **pass/fail mandatory gates**, not a score that attractive UX can offset.

| Mandatory gate | Evidence needed |
|---|---|
| **All components on-prem / no cloud dependency** | Architecture diagram; block outbound internet access during a complete start-run-approve-resume cycle; inspect telemetry, update checks and licensing calls. |
| **Approved license and support** | Exact server + UI + SDK + connectors licenses; legal approval for internal commercial use; enterprise support / SLA options and version lifecycle. |
| **Corporate identity and permissions** | Corporate OIDC/SAML/AD integration; enforced RBAC/ABAC at **APIs**, not only UI; approver identity; segregation of duties. |
| **Durable approvals** | Remains paused across restarts and deployment changes; timeout, escalation, cancel, reject and duplicate-approval semantics. |
| **Audit and data protection** | Configurable retention/redaction, workflow history, export to SIEM, encryption in transit/at rest, tamper-evident approval history. |
| **Operating model** | HA, backup/restore, disaster recovery, monitoring, disaster-recovery test, upgrades/versioned long-running flows. |
| **Approved software integration** | Works through available internal REST/message brokers and approved language/container stack; no forbidden external model API. |

Then score candidates **1–5 after a POC** with *illustrative weights* (adjust with security/platform owners):

| Weighted dimension | Weight | Evidence to score |
|---|---:|---|
| Durable recovery, retries, waiting, safe execution | 25% | Forced worker/service crashes, recovered state, duplicate-action prevention |
| Human approvals, authorization and governance | 25% | Dashboard integration, RBAC, maker-checker, audit trail |
| Security, on-prem operability and disaster recovery | 20% | Air-gap test, deployment/upgrade/backups/restore, SSO integration |
| Developer fit + ecosystem | 15% | SDK match, code reviewability, testing and debugging |
| Cost / license / operational ownership | 15% | Vendor quote + HA footprint + support burden |

**Do not publish numeric winner scores yet:** without measured proof, numbers imply precision the team does not have. A candidate failing a hard gate is excluded even if it excels elsewhere.

---

## 7. Practical proof of concept (same use case on 3 engines)

Use **Temporal, Camunda, Restate**, with Inngest as an optional fourth if the team prizes event-driven simplicity.

**Common test fixture:** A fabricated security vulnerability event comes into an internal API. The workflow enriches it, invokes a mock/internal LLM to propose a remediation, applies a deterministic severity/policy rule, pauses for an analyst approval in the **existing dashboard**, and either safely executes a mock remediation or records rejection. No live production changes.

**Pass/fail exercises:**

1. **No internet:** Run the entire stack with outbound traffic denied; verify all dependencies, model endpoints, admin consoles, auth and telemetry are internal.
2. **Long wait:** Pause approval for 48 hours in test (or simulate advanced time), deploy a new worker version, restart nodes, and verify the exact case still resumes.
3. **Crashes:** Kill the worker midway through an LLM step, then after the mock action returns but before its success is recorded. Measure duplicate attempts and enforce idempotency.
4. **Unauthorized approval:** Analyst from the wrong group and the original requester both attempt approval; backend must deny and produce audit evidence. Test simultaneous and duplicate clicks.
5. **Governance:** Query who approved what, which data/policy/model led to it, and which outcome was verified. Export to SIEM; redact sensitive values.
6. **Day-2 ops:** Test backup/restore, queue backlog, stuck workflows, replay/reset, workflow schema/version migration, and failure/latency dashboards.
7. **Cost and DX:** Count deployable components, engineer-hours, code needed for approval UX, and HA resources. Compare actual experience, not vendors' cloud benchmarks.

**Definition of success:** Approvals never disappear or bypass authorization; completed steps are not blindly repeated; partial failures are reconciled; security evidence is retrievable; **all data/control components stay in the allowed network**.

---

## 8. Decision tree — what to recommend in the meeting

- **We want a reliable invisible engine behind a custom dashboard, across languages, for many years:** **Temporal**. This is the default architectural recommendation.
- **We want a process platform with business-readable flowcharts, native human work queues/forms and first-class people/system coordination:** **Camunda**. Accept paid on-prem production licensing and confirm per-task authorization in the chosen version.
- **We want the most developer-lightweight durable backend and are willing to validate a newer stack:** **Restate**. Serious head-to-head candidate; verify BSL suitability and hardening.
- **We want event-driven functions and already serve our workflows over internal HTTP:** **Inngest** only once self-host production support/HA and SSPL terms satisfy security/legal.
- **We only need TS background tasks:** **Trigger.dev / Workflow SDK** may be simpler *locally*, but are not my first choice for an enterprise-wide approval backbone—especially with Trigger's self-host checkpoint gap.
- **The main task becomes evaluation of Python agents or ML pipelines, rather than human workflow control:** use **Kitaru/ZenML alongside**, not instead of, the orchestrator.

**Recommended meeting decision:** Approve a **requirements and POC phase** with **Temporal as incumbent favorite**, **Camunda as the approval/process benchmark**, and **Restate as the lightweight technical benchmark**. Defer a final product standardization decision until deployment policy, licensing and tests are resolved.

---

## 9. Questions to take to requirements gathering

**Product/architecture:** What exact first workflow is being automated? Is it one security-dashboard team or a shared enterprise platform? Are workflows mostly event-driven, scheduled, or dynamic AI agents? What runtime languages are actually approved? Is the existing UI mandatory for every approval?

**Security:** Does on-prem mean **physically in a data centre / fully air-gapped**, or may approved internal private infrastructure be used? Which IdP, database, K8s/VM/container platform, message bus, secrets vault, logging/SIEM and internal LLM endpoint already exist? May software call a license/telemetry endpoint? Are approval decisions subject to dual-control/maker-checker rules?

**Operations/procurement:** Who owns stateful services and backups? Required concurrent executions, event rate, backlog tolerance, workflow duration, retention, RTO/RPO and support SLA? Are commercial licenses acceptable? Which components must be FIPS-validated or formally approved for software supply chain?

**Decision-changing answers:** If **no stateful platform operations team**, Temporal's operational burden matters more. If **the organization insists on ready-made user tasks**, Camunda rises. If **licensing prohibits SSPL/BSL** or if **zero vendor egress** is mandatory, certain candidates narrow quickly.

---

## 10. Source quality, date notes, and further reading

Research checked **15 October 2026**. Prefer the **official self-hosting, licensing, and security documents** over vendor-authored “versus Temporal” pages. The supplied links to **Akka** and **ZenML** are blog comparisons, not evidence that those products are direct substitutes; ZenML's July article additionally reflects an older Kitaru focus.

**Original links supplied:** [Inngest comparison](https://www.inngest.com/compare-to-temporal) · [Akka comparison article](https://akka.io/blog/inngest-vs-temporal) · [ZenML comparison article](https://www.zenml.io/blog/inngest-vs-temporal) · [Camunda](https://camunda.com/) · [Trigger.dev comparison](https://trigger.dev/vs/temporal) · [Restate comparison](https://restate.dev/vs/temporal) · [Workflow SDK comparison](https://workflow-sdk.dev/docs/comparisons/workflow-sdk-vs-temporal) · [Prismatic](https://prismatic.io/).

**Claims specifically verified against primary sources:**

- Temporal: [production/self-host architecture](https://docs.temporal.io/self-hosted-guide), [signals/updates](https://docs.temporal.io/encyclopedia/workflow-message-passing), [UI auth vs backend authorization](https://docs.temporal.io/references/web-ui-environment-variables).
- Camunda: [production self-managed enterprise license](https://camunda.com/pricing/), [8.8 Tasklist V2 limitations](https://docs.camunda.io/docs/8.8/components/tasklist/api-versions/), [8.9 task authorization](https://docs.camunda.io/docs/8.9/components/tasklist/user-task-authorization/).
- Restate: [self-host architecture](https://restate.dev/vs/temporal), [BSL license and internal production use grant](https://github.com/restatedev/restate/blob/main/LICENSE).
- Inngest: [self-host production caveats](https://www.inngest.com/docs/platform-and-operations/self-host-inngest), [server/SDK license split](https://github.com/inngest/inngest).
- Trigger.dev: [Cloud vs self-host feature matrix](https://trigger.dev/docs/self-hosting/overview).
- Workflow SDK: [production-ready self-host Postgres World](https://workflow-sdk.dev/worlds/postgres).
- Akka: [self-managed ops](https://doc.akka.io/operations/configuring.html), [BSL commercial-use FAQ](https://akka.io/bsl-license-faq).
- ZenML/Kitaru: [current product definitions](https://github.com/zenml-io/zenml/blob/main/docs/book/introduction.md), [current Kitaru repository](https://github.com/zenml-io/kitaru).
- Prismatic: [on-prem agent sends traffic to Prismatic platform](https://prismatic.io/docs/integrations/connections/on-prem-agent/).

**Scope limit:** This is a **documented capability comparison** and architectural recommendation, not a tested penetration review, paid license quote, production benchmark or company-approved design. Validate versions and contracts before relying on them as procurement commitments.
