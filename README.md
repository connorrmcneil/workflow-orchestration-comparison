# Workflow Orchestration Comparison

An evaluation of workflow orchestration engines for backend jobs, human-approval processes and AI-agent workflows, under one hard constraint: everything runs on-prem on our own Kubernetes.

**Recommendation:** Temporal, self-hosted, proven with a two-week proof of concept. Camunda is the pick if business-owned process diagrams or a vendor SLA matter more than licence cost; Restate is the lightest to run but needs licence and vendor review.

## Contents

| File | What it covers |
| --- | --- |
| [docs/01-on-prem-comparison.md](docs/01-on-prem-comparison.md) | All nine tools: requirements, five kinds of tool, side-by-side table, pros and cons of each, recommendation |
| [docs/02-temporal-camunda-restate.md](docs/02-temporal-camunda-restate.md) | The three finalists in depth, and one example job built three ways (BPMN model vs Temporal code vs Restate code) |
| [docs/images/](docs/images/) | The diagrams used in both docs |

Tools compared: Temporal, Camunda, Restate, Akka, Inngest, Trigger.dev, Workflow SDK (Vercel), ZenML, Prismatic.

Researched October 15, 2026. Licence, self-hosting and pricing details change; check the linked sources before relying on them.
