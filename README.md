# Workflow Orchestration Comparison

An evaluation of workflow orchestration engines for backend jobs, human-approval processes and AI-agent workflows, under one hard constraint: everything runs on-prem on our own Kubernetes.

**Recommendation:** Temporal, self-hosted, proven with a two-week proof of concept. Camunda is the pick if business-owned process diagrams or a vendor SLA matter more than licence cost; Restate is the lightest to run but needs licence and vendor review.

## Contents

| File | What it covers |
| --- | --- |
| [docs/01-on-prem-comparison.md](docs/01-on-prem-comparison.md) | All nine tools: requirements, five kinds of tool, side-by-side table, pros and cons of each, recommendation |
| [docs/02-temporal-camunda-restate.md](docs/02-temporal-camunda-restate.md) | The three finalists in depth, and one example job built three ways (BPMN model vs Temporal code vs Restate code) |
| [docs/images/](docs/images/) | The diagrams used in both docs |
| [docs/briefs/orchestration_meeting_one_pager.md](docs/briefs/orchestration_meeting_one_pager.md) | One-page meeting summary: POC recommendation, core trade-offs, questions to resolve, 30-second pitch |
| [docs/briefs/on_prem_orchestration_three_way_meeting_brief.md](docs/briefs/on_prem_orchestration_three_way_meeting_brief.md) | Temporal vs Restate vs Camunda 8 meeting brief: how each is built, parallelism and scale questions, security gates, POC test plan |
| [docs/briefs/on_prem_agentic_orchestration_comparison.md](docs/briefs/on_prem_agentic_orchestration_comparison.md) | Full technology comparison for the security-dashboard use case: all options, recommended architecture, selection criteria, decision tree |

Tools compared: Temporal, Camunda, Restate, Akka, Inngest, Trigger.dev, Workflow SDK (Vercel), ZenML, Prismatic.

Researched October 15, 2026. Licence, self-hosting and pricing details change; check the linked sources before relying on them.
