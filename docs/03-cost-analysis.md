# Cost Analysis: Temporal vs Camunda vs Restate

October 16, 2026 · Connor McNeil

Three-year total cost of ownership (TCO) for running each finalist self-hosted on our own Kubernetes. All figures are in Canadian dollars. Every cost figure is calculated by [`cost-model/model.py`](../cost-model/model.py). Swap in the bank's own rates there and re-run it to get our real number.

## Bottom line

**Base case over three years: Restate about $270k, Temporal about $384k, Camunda about $1.16M.**

- **Camunda's cost is mostly its licence.** The licence is about 64% of Camunda's total, and its price is not published. Our placeholder is US$175k a year. Even with a free licence, Camunda's base case would still cost about $33k more than Temporal over three years, because it has more infrastructure to run.
- **For Temporal and Restate, people are the cost, not servers.** Building and operating the platform is about 80% of their totals. Adding a quarter of an engineer to operations ($117k over three years) costs more than Temporal's entire three-year infrastructure bill ($82k).
- **The extra money for Camunda buys something real.** It pays for 24x7 vendor support with an SLA, plus a built-in task inbox, forms, roles and an audit log. Temporal sells no support for self-hosted deployments, and we found no self-hosted support offering from Restate.
- **The biggest unknown is the Camunda quote.** Get one before the decision. Across our placeholder range (US$65k–330k a year), the licence alone moves Camunda's three-year total by more than $1M.

## 3-year total cost

| | Low | Base | High |
| --- | ---: | ---: | ---: |
| Temporal | $186k | $384k | $841k |
| Camunda | $448k | $1,162k | $2,275k |
| Restate | $135k | $270k | $639k |

The low and high columns set every input to its low or high value at once. They show the outer bounds, not likely outcomes. The base case is the planning number.

## Where the money goes (base case, 3 years)

| Category | Temporal | Camunda | Restate |
| --- | ---: | ---: | ---: |
| One-time build (tool-specific work) | $68k | $58k | $58k |
| Licence (3 years) | $0 | $745k | $0 |
| Infrastructure (3 years) | $82k | $125k | $49k |
| Platform operations staff (3 years) | $234k | $234k | $164k |
| **Total** | **$384k** | **$1,162k** | **$270k** |
| People's share (build + operations) | 79% | 25% | 82% |

**Year by year (base case)**

| | Year 1 | Year 2 | Year 3 | 3 years |
| --- | ---: | ---: | ---: | ---: |
| Temporal | $173k | $105k | $105k | $384k |
| Camunda | $426k | $368k | $368k | $1,162k |
| Restate | $129k | $71k | $71k | $270k |

Year 1 includes the one-time build. From year 2 onward each tool settles at its annual run rate. That rate is licence, infrastructure and operations staff. Figures are rounded to the nearest thousand, so rows may not add exactly.

## The line items

### 1. Licence and vendor support

| | Licence for our use | Price used in the model (per year) | Vendor support for self-hosted |
| --- | --- | --- | --- |
| Temporal | MIT, free | $0 | None sold. Self-hosted gets community Slack and the forum only; paid support tiers are Temporal Cloud only |
| Camunda | Enterprise licence required for production | US$65k / 175k / 330k (low / base / high) | Included: 24x7 support with SLAs, Customer Success, training |
| Restate | BSL 1.1; internal production use is free, pending legal review | $0 | None found. Paid plans are Restate Cloud and BYOC, and BYOC runs only in AWS or GCP |

**About the Camunda figures.** Camunda publishes no Self-Managed price, so these are placeholders until we get a quote:

- **Base (US$175k):** the list price of Camunda's SaaS "Enterprise Plan" on AWS Marketplace, US$175,000 per 12 months. That is SaaS, so a Self-Managed quote could differ in either direction.
- **High (US$330k):** a figure a user cited on Camunda's forum. Camunda staff said it reflected "hundreds of thousands – if not millions – of processes" and was not a minimum price.
- **Low (US$65k):** a low-credibility third-party estimate with no source.
- **How pricing likely works:** Camunda's docs say licensing "does not depend on the provisioned hardware resources". The Marketplace listing meters "Process Instances", so pricing is likely volume-based. That is an inference. Ask Camunda to price at our expected volume.
- **One licence for every environment:** the model assumes the licence covers non-production and DR. Confirm this with Camunda.

### 2. Infrastructure

**Method.** We take a modest high-availability production footprint for each tool (from vendor docs and Helm charts). We convert it to standard 4 vCPU / 16 GB nodes, taking whichever of CPU or memory needs more nodes, and add 30% for Kubernetes overhead and headroom. Then we multiply by the number of environments and by a unit rate.

**Production footprint (base case)**

| Tool | Components | vCPU | RAM | Disk | Node-equivalents (with headroom) |
| --- | --- | ---: | ---: | ---: | ---: |
| Temporal | Server (frontend, history, matching, worker, Web UI) 9 vCPU / 22 GB; PostgreSQL HA 2 × 4 vCPU / 16 GB / 500 GB; OpenSearch 3 × 2 vCPU / 8 GB / 100 GB | 23 | 78 GB | 1.3 TB | 7.5 |
| Camunda | Orchestration cluster 3 brokers × 3 vCPU / 4 GB / 64 GB; Connectors, Identity, Keycloak, Optimize 2.4 vCPU / 2.9 GB; Elasticsearch 3 × 7 vCPU / 8 GB / 256 GB; PostgreSQL HA for Keycloak 2 × 2 vCPU / 8 GB / 100 GB | 36.4 | 54.9 GB | 1.16 TB | 11.8 |
| Restate | Restate cluster 3 × 4 vCPU / 8 GB / 64 GB; MinIO for snapshots 4 × 0.5 vCPU / 2 GB / 100 GB | 14 | 32 GB | 0.6 TB | 4.6 |

Notes on the footprints:

- **Temporal:** server sizing follows Temporal's published small production cluster: 2 frontend pods at 1 vCPU / 1 GB, 2 history pods at 2 vCPU / 8 GB, 2 matching pods at 1 vCPU / 1 GB, and 512 history shards. The low case drops OpenSearch and uses PostgreSQL for visibility; Temporal supports that but recommends Elasticsearch or OpenSearch beyond small volumes. The high case gives PostgreSQL 32 GB per node, matching Temporal's benchmark database.
- **Camunda:** the base case is Camunda's documented 8.9 baseline with Elasticsearch and Optimize. It is sized for 51 process instances a second, far above our need, but three brokers is the high-availability minimum. The low case uses the new 8.9 PostgreSQL secondary storage without Optimize (about 14 vCPU / 22 GB). That option has about 70% of Elasticsearch's write throughput and does not support Optimize. The Keycloak database is our assumption.
- **Restate:** node sizing is the Helm chart default request (4 vCPU / 8 GB). Three nodes tolerate one failure. Snapshots need S3-compatible storage; MinIO needs at least four replicas, or we can use an object store the bank already runs. The high case sizes nodes to the chart's 6-vCPU limit.

**Unit rates**

| Input | Low | Base | High | Basis |
| --- | ---: | ---: | ---: | --- |
| Cost of a 4 vCPU / 16 GB node, per month | $93 | $140 | $233 | AWS m7i.xlarge, ca-central-1, on-demand US$0.2247/h × 730 h × 1.4196 = $233. Private cloud assumed at 40% / 60% / 100% of that |
| Block storage, per GB-month | $0.050 | $0.075 | $0.125 | AWS gp3, ca-central-1, US$0.088, scaled the same way |
| Environments | 1.5× | 2× | 3× | Production plus non-production (low); plus partial DR (base); plus full DR (high) |

**Annual infrastructure cost**

| | Low | Base | High |
| --- | ---: | ---: | ---: |
| Temporal | $10k | $27k | $81k |
| Camunda | $8k | $42k | $104k |
| Restate | $8k | $16k | $57k |

The 40% private-cloud factor is our assumption, informed by a vendor-funded VMware study that put private cloud at about 30% of public cloud cost per VM. The bank's internal chargeback rate should replace all three factors.

### 3. Platform operations staff

The people who run the engine: installs, upgrades, patching, backups, on-call and incident response.

**Cost of one engineer, fully loaded**

| | Low | Base | High |
| --- | ---: | ---: | ---: |
| Base salary | $105,000 | $120,000 | $140,000 |
| Loaded multiplier (benefits, CPP/EI, overhead) | 1.25 | 1.30 | 1.40 |
| Cost per year | $131,250 | $156,000 | $196,000 |
| Cost per person-week (46 working weeks) | $2,853 | $3,391 | $4,261 |

Salary basis:

- Robert Half 2027 guide: site reliability engineer midpoint $111,499 in Halifax and $128,790 in Toronto.
- Payscale: senior software engineer in Halifax, average $99,505.
- Indeed: senior software engineer in Toronto, average $141,554 (October 2026).
- Levels.fyi: RBC senior (PL08) total compensation about $114k.
- Loaded multipliers of 1.2–1.4 are typical, and bank pensions and bonuses push toward the top of that range.

**Operations staffing per tool (FTE per year)**

| | Low | Base | High | Why |
| --- | ---: | ---: | ---: | --- |
| Temporal | 0.30 | 0.50 | 0.80 | Four services plus PostgreSQL and OpenSearch; upgrades one minor version at a time; no vendor support to escalate to |
| Camunda | 0.30 | 0.50 | 0.75 | The most components, and the architecture changed in each of 8.8, 8.9 and 8.10; offset by 24x7 vendor support |
| Restate | 0.20 | 0.35 | 0.60 | One binary with no external database; but a young product with breaking changes in point releases, and no vendor support |

These FTE figures are judgments, not measurements. The proof of concept should replace them with what the team observes.

### 4. One-time build (tool-specific work only)

Person-weeks, low / base / high.

| Tool | Work item | Person-weeks |
| --- | --- | ---: |
| Temporal | Install and harden the platform (Helm, PostgreSQL, OpenSearch, DR runbook) | 5 / 8 / 12 |
| | Security: mTLS, SSO-linked authorizer, Web UI login, audit log pipeline | 4 / 6 / 9 |
| | Approval inbox in our React app (queue, assignment, escalation view) | 4 / 6 / 9 |
| | **Total** | **13 / 20 / 30** |
| Camunda | Install and harden the platform (Helm, Elasticsearch, Keycloak, DR runbook) | 5 / 8 / 13 |
| | Connect Identity to bank SSO; configure roles and task authorization | 2 / 3 / 5 |
| | Embed the Tasklist API and forms in our React app | 2 / 3 / 5 |
| | BPMN learning curve for the team | 1 / 3 / 4 |
| | **Total** | **10 / 17 / 27** |
| Restate | Install and harden the cluster (operator, MinIO, DR runbook) | 3 / 5 / 8 |
| | Security: auth gateway, network policies, admin UI access | 3 / 4 / 6 |
| | Audit export from the journal | 1 / 2 / 4 |
| | Approval inbox in our React app (queue, assignment, escalation view) | 4 / 6 / 9 |
| | **Total** | **11 / 17 / 27** |

At the base rate this is $68k for Temporal and $58k each for Camunda and Restate. Temporal's official courses, such as Temporal 102, are free. Camunda certification is offered only to customers and partners, at an unpublished price.

### 5. Costs left out of the model

These are the same for all three tools, or have no price we could find. Budget for them separately.

- **Internal LLM inference.** This is probably the largest variable cost in the whole system, and it doesn't depend on which engine we pick.
- **Writing the business workflows themselves**, and the security dashboard.
- **Shared platform services we assume already exist:** the Kubernetes control plane, monitoring and logging, SIEM, the identity provider and backup tooling.
- **Legal review** of Restate's BSL licence, and procurement effort for the Camunda contract.
- **Commercial support for dependencies, if bank policy requires it.**
  - Camunda's base case runs three Elasticsearch nodes. Elastic Platinum is about US$6,800 per node per year at list (third-party estimate), so roughly US$20k a year extra. OpenSearch, or Camunda's PostgreSQL option, avoids it.
  - MinIO AIStor and EDB Postgres support prices are unpublished.
- **The proof of concept:** two engineers for two weeks is about $14k at the base rate.

## What moves the answer

1. **The Camunda licence.**
   - Each US$50k a year changes Camunda's three-year total by about $213k.
   - With a free licence, Camunda's base case would be $417k, against $384k for Temporal.
2. **Operations staffing.**
   - Each extra 0.25 FTE adds $117k over three years at the base rate.
   - This matters most for Temporal and Restate, where operations staff are about 60% of the total (about 80% including the build).
3. **The internal infrastructure rate.**
   - Going from 60% to 100% of cloud list prices adds $55k to Temporal, $84k to Camunda and $33k to Restate over three years.
4. **Volume.**
   - At our expected load (about 0.2 workflow starts a second), we expect all three footprints to be far larger than we need, so infrastructure should barely grow with volume. The proof of concept should confirm this.
   - Camunda's licence probably does grow with volume, so price it at a realistic three-year forecast.

## What the money buys

| Compared with Temporal (base case) | Difference | What it buys or costs us |
| --- | --- | --- |
| Camunda | About $778k more over 3 years (about $263k a year at run rate) | 24x7 vendor support with an SLA, a native task inbox and forms, roles and an audit log out of the box, Optimize reporting, and process diagrams the business can read |
| Restate | About $114k less over 3 years | Mostly lighter operations. The trade-offs: a BSL licence to clear with legal, a younger vendor, no built-in authentication, and no vendor support |

## Cost per workflow run (illustrative)

Assume 1,000 users × 5 runs a day × 250 working days, which is 1.25 million runs a year. At the base annual run rate (excluding the one-time build and LLM inference), a run costs about $0.08 on Temporal, $0.29 on Camunda and $0.06 on Restate.

## Making this the bank's number

Open [`cost-model/model.py`](../cost-model/model.py) and replace these inputs with our own:

1. Internal chargeback for compute and storage. For a rate in Canadian dollars, set `NODE_CAD_MONTH` and `BLOCK_CAD_GB_MONTH` directly and `rate` to 1.0; `NODE_USD_MONTH` expects US dollars and is converted.
2. Environment count (`env`).
3. Loaded salary (`salary`, `loaded`).
4. Camunda's quote (`LIC_USD`).
5. Operations FTE and build estimates, after the proof of concept.

Then run `python3 cost-model/model.py`. Use `--json` to see every intermediate figure.

## Sources

Checked October 15–16, 2026.

**Licence and support**
- [Camunda pricing](https://camunda.com/pricing) · [Camunda licences (8.9 docs)](https://raw.githubusercontent.com/camunda/camunda-docs/main/versioned_docs/version-8.9/reference/licenses.md) · [Camunda SaaS Enterprise Plan on AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-6y664fcnydiqg) · [Camunda forum thread on 8.6 licence costs](https://forum.camunda.io/t/how-do-you-handle-the-additional-costs-of-the-new-8-6-licence/59765) · [Third-party Camunda pricing estimate (low credibility)](https://automationatlas.io/answers/camunda-pricing-explained-2026/) · [Camunda certification](https://camunda.com/services/certification/)
- [Temporal pricing](https://temporal.io/pricing) · [Temporal Cloud pricing docs](https://docs.temporal.io/cloud/pricing) · [Temporal forum: paid support](https://community.temporal.io/t/do-you-offer-paid-support-service/1593) · [Temporal 102 course (free)](https://learn.temporal.io/courses/temporal_102/)
- [Restate Cloud pricing](https://www.restate.dev/cloud) · [Restate BYOC overview](https://docs.restate.dev/byoc/overview) · [Restate licence](https://github.com/restatedev/restate/blob/main/LICENSE)

**Sizing**
- [Temporal Helm chart values](https://github.com/temporalio/helm-charts/blob/main/charts/temporal/values.yaml) · [Scaling Temporal: the basics](https://temporal.io/blog/scaling-temporal-the-basics) · [Temporal visibility](https://docs.temporal.io/self-hosted-guide/visibility)
- [Camunda 8.9 Self-Managed sizing](https://raw.githubusercontent.com/camunda/camunda-docs/main/versioned_docs/version-8.9/components/best-practices/architecture/sizing-self-managed.md) · [Camunda RDBMS benchmark results](https://raw.githubusercontent.com/camunda/camunda-docs/main/versioned_docs/version-8.9/self-managed/concepts/secondary-storage/rdbms-benchmark-results.md) · [Camunda 8.9 Helm values](https://github.com/camunda/camunda-platform-helm/blob/main/charts/camunda-platform-8.9/values.yaml)
- [Restate Helm values](https://github.com/restatedev/restate/blob/main/charts/restate-helm/values.yaml) · [Restate replicated values](https://github.com/restatedev/restate/blob/main/charts/restate-helm/replicated-values.yaml) · [Restate clusters](https://docs.restate.dev/server/clusters) · [Restate on Kubernetes](https://docs.restate.dev/server/deploy/kubernetes)

**Rates**
- [Bank of Canada exchange rates (USD/CAD 1.4196, Oct 15, 2026)](https://www.bankofcanada.ca/?p=190892)
- [AWS ca-central-1 prices: m7i.xlarge, gp3 (third-party tracker)](https://aws-pricing.com/ca-central-1.html) · [VMware VCF TCO study (vendor-funded)](https://www.vmware.com/docs/vmw-vcf-tco-whitepaper)
- [Robert Half: SRE salary, Halifax](https://roberthalf.com/ca/en/job-details/site-reliability-engineer/halifax-ns) · [Robert Half: SRE salary, Toronto](https://roberthalf.com/ca/en/job-details/site-reliability-engineer/toronto-on) · [Payscale: senior software engineer, Halifax](https://www.payscale.com/research/CA/Job=Senior_Software_Engineer/Salary/186b6b8a/Halifax-NS) · [Indeed: software engineer salaries, Toronto](https://ca.indeed.com/career/software-engineer/salaries/Toronto--ON) · [Levels.fyi: RBC](https://www.levels.fyi/companies/rbc/salaries/software-engineer?country=43) · [Fully burdened labour rate](https://runway.com/resources/glossary/fully-burdened-labor-rate) · [Job Bank: software engineer wages, Halifax](https://www.jobbank.gc.ca/marketreport/wages-occupation/5482/22390)
- [Elastic pricing estimate (third-party)](https://vendorbenchmark.com/vendors/elastic-elasticsearch-pricing) · [MinIO AIStor tiers](https://www.min.io/blog/introducing-new-subscription-tiers-for-minio-aistor-free-enterprise-lite-and-enterprise)

**Caveats.** Several cloud prices come from third-party price trackers, because the official AWS and Azure pricing pages could not be fetched directly. Camunda's price is a placeholder. FTE and build estimates are engineering judgments. This is a planning model, not a quote or a procurement figure.
