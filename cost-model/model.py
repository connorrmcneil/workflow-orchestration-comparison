"""3-year TCO model: Temporal vs Camunda 8 Self-Managed vs Restate, self-hosted.
All outputs in CAD. Every input is listed in INPUTS so it can be swapped for bank rates."""
import json

FX = 1.4196  # USD->CAD, Bank of Canada, 15 Oct 2026
YEARS = 3

# Unit rates ----------------------------------------------------------------
# Node-equivalent = 4 vCPU / 16 GB (AWS m7i.xlarge, ca-central-1, on-demand $0.2247/h)
NODE_USD_MONTH = 0.2247 * 730
NODE_CAD_MONTH = NODE_USD_MONTH * FX
BLOCK_CAD_GB_MONTH = 0.088 * FX  # gp3 ca-central-1
HEADROOM = 0.30  # Kubernetes overhead / spare capacity on top of requests

SCEN = {
    #            on-prem cost vs cloud list, environment multiplier, salary, loaded multiplier
    "low":  {"rate": 0.40, "env": 1.5, "salary": 105_000, "loaded": 1.25},
    "base": {"rate": 0.60, "env": 2.0, "salary": 120_000, "loaded": 1.30},
    "high": {"rate": 1.00, "env": 3.0, "salary": 140_000, "loaded": 1.40},
}
WORK_WEEKS = 46

# Production footprints (vCPU, RAM GB, block GB) ------------------------------
FOOT = {
    "Temporal": {
        "low":  [("Temporal server (frontend, history, matching, worker, web)", 9, 22, 0),
                 ("PostgreSQL HA: 2 x 4 vCPU / 16 GB / 500 GB (also visibility)", 8, 32, 1000)],
        "base": [("Temporal server (frontend, history, matching, worker, web)", 9, 22, 0),
                 ("PostgreSQL HA: 2 x 4 vCPU / 16 GB / 500 GB", 8, 32, 1000),
                 ("OpenSearch visibility: 3 x 2 vCPU / 8 GB / 100 GB", 6, 24, 300)],
        "high": [("Temporal server (frontend, history, matching, worker, web)", 9, 22, 0),
                 ("PostgreSQL HA: 2 x 4 vCPU / 32 GB / 500 GB", 8, 64, 1000),
                 ("OpenSearch visibility: 3 x 2 vCPU / 8 GB / 100 GB", 6, 24, 300)],
    },
    "Camunda": {
        "low":  [("Orchestration cluster + PostgreSQL secondary storage, no Optimize (8.9 RDBMS)", 14, 22, 450)],
        "base": [("Orchestration cluster: 3 brokers x 3 vCPU / 4 GB / 64 GB", 9, 12, 192),
                 ("Connectors, Identity, Keycloak, Optimize", 2.4, 2.9, 0),
                 ("Elasticsearch: 3 x 7 vCPU / 8 GB / 256 GB", 21, 24, 768),
                 ("PostgreSQL HA for Identity/Keycloak: 2 x 2 vCPU / 8 GB / 100 GB", 4, 16, 200)],
        "high": [("Orchestration cluster: 3 brokers x 3 vCPU / 4 GB / 64 GB", 9, 12, 192),
                 ("Connectors, Identity, Keycloak, Optimize", 2.4, 2.9, 0),
                 ("Elasticsearch: 3 x 7 vCPU / 8 GB / 256 GB", 21, 24, 768),
                 ("PostgreSQL HA for Identity/Keycloak: 2 x 2 vCPU / 8 GB / 100 GB", 4, 16, 200)],
    },
    "Restate": {
        "low":  [("Restate cluster: 3 x 4 vCPU / 8 GB / 64 GB", 12, 24, 192),
                 ("MinIO snapshots: 4 x 0.5 vCPU / 2 GB / 100 GB", 2, 8, 400)],
        "base": [("Restate cluster: 3 x 4 vCPU / 8 GB / 64 GB", 12, 24, 192),
                 ("MinIO snapshots: 4 x 0.5 vCPU / 2 GB / 100 GB", 2, 8, 400)],
        "high": [("Restate cluster: 3 x 6 vCPU / 8 GB / 64 GB (sized to limits)", 18, 24, 192),
                 ("MinIO snapshots: 4 x 0.5 vCPU / 2 GB / 100 GB", 2, 8, 400)],
    },
}

# Licence (USD/year) ---------------------------------------------------------
LIC_USD = {
    "Temporal": {"low": 0, "base": 0, "high": 0},
    "Camunda":  {"low": 65_000, "base": 175_000, "high": 330_000},
    "Restate":  {"low": 0, "base": 0, "high": 0},
}

# Platform operations FTE per year (run, patch, upgrade, on-call share) -------
OPS_FTE = {
    "Temporal": {"low": 0.30, "base": 0.50, "high": 0.80},
    "Camunda":  {"low": 0.30, "base": 0.50, "high": 0.75},
    "Restate":  {"low": 0.20, "base": 0.35, "high": 0.60},
}

# One-time build, person-weeks: tool-specific work only -----------------------
BUILD_PW = {
    "Temporal": {
        "Install and harden the platform (Helm, PostgreSQL, OpenSearch, DR runbook)": (5, 8, 12),
        "Security: mTLS, SSO-linked authorizer, Web UI login, audit log pipeline": (4, 6, 9),
        "Approval inbox in our React app (queue, assignment, escalation view)": (4, 6, 9),
    },
    "Camunda": {
        "Install and harden the platform (Helm, Elasticsearch, Keycloak, DR runbook)": (5, 8, 13),
        "Connect Identity to bank SSO; configure roles and task authorization": (2, 3, 5),
        "Embed Tasklist API and forms in our React app": (2, 3, 5),
        "BPMN learning curve for the team": (1, 3, 4),
    },
    "Restate": {
        "Install and harden the cluster (operator, MinIO, DR runbook)": (3, 5, 8),
        "Security: auth gateway, network policies, admin UI access": (3, 4, 6),
        "Audit export from the journal": (1, 2, 4),
        "Approval inbox in our React app (queue, assignment, escalation view)": (4, 6, 9),
    },
}
IDX = {"low": 0, "base": 1, "high": 2}


def run():
    out = {}
    for tool in FOOT:
        out[tool] = {}
        for s, p in SCEN.items():
            rows = FOOT[tool][s]
            vcpu = sum(r[1] for r in rows)
            ram = sum(r[2] for r in rows)
            disk = sum(r[3] for r in rows)
            nodes_prod = max(vcpu / 4, ram / 16) * (1 + HEADROOM)
            compute_yr = nodes_prod * p["env"] * NODE_CAD_MONTH * p["rate"] * 12
            storage_yr = disk * p["env"] * BLOCK_CAD_GB_MONTH * p["rate"] * 12
            infra_yr = compute_yr + storage_yr
            fte_cost = p["salary"] * p["loaded"]
            ops_yr = OPS_FTE[tool][s] * fte_cost
            lic_yr = LIC_USD[tool][s] * FX
            pw = sum(v[IDX[s]] for v in BUILD_PW[tool].values())
            build = pw * fte_cost / WORK_WEEKS
            annual = lic_yr + infra_yr + ops_yr
            total = build + YEARS * annual
            out[tool][s] = dict(vcpu=vcpu, ram=ram, disk=disk, nodes_prod=nodes_prod,
                                compute_yr=compute_yr, storage_yr=storage_yr, infra_yr=infra_yr,
                                ops_fte=OPS_FTE[tool][s], ops_yr=ops_yr, lic_yr=lic_yr,
                                build_pw=pw, build=build, annual=annual, tco=total,
                                fte_cost=fte_cost, pw_cost=fte_cost / WORK_WEEKS)
    # Break-even Camunda licence vs Temporal (base): licence that makes 3-yr TCO equal
    b = out
    t, c = b["Temporal"]["base"], b["Camunda"]["base"]
    c_no_lic = c["tco"] - YEARS * c["lic_yr"]
    breakeven_cad = (t["tco"] - c_no_lic) / YEARS
    out["_breakeven_camunda_licence_cad_per_year"] = breakeven_cad
    out["_breakeven_camunda_licence_usd_per_year"] = breakeven_cad / FX
    out["_node_cad_month"] = NODE_CAD_MONTH
    out["_block_cad_gb_month"] = BLOCK_CAD_GB_MONTH
    # POC cost: 2 engineers x 2 weeks, base rate
    pwc = SCEN["base"]["salary"] * SCEN["base"]["loaded"] / WORK_WEEKS
    out["_poc_base"] = 4 * pwc
    # Sensitivity on base: added 3-year cost of 0.25 more operations FTE
    out["_ops_plus_quarter_fte_3yr"] = 0.25 * SCEN["base"]["salary"] * SCEN["base"]["loaded"] * YEARS
    return out


def report(r):
    tools = ["Temporal", "Camunda", "Restate"]
    k = lambda v: f"{v / 1000:,.0f}k"
    print("3-year TCO, CAD")
    print(f"{'':10}{'low':>10}{'base':>10}{'high':>10}")
    for t in tools:
        print(f"{t:10}" + "".join(f"{k(r[t][s]['tco']):>10}" for s in ("low", "base", "high")))
    print("\nBase case, 3 years, by category (CAD)")
    for t in tools:
        x = r[t]["base"]
        print(f"{t:10} build {k(x['build']):>6}  licence {k(3 * x['lic_yr']):>6}  "
              f"infra {k(3 * x['infra_yr']):>6}  ops {k(3 * x['ops_yr']):>6}  total {k(x['tco']):>6}")
    print(f"\nCamunda base TCO with a free licence: {k(r['Camunda']['base']['tco'] - 3 * r['Camunda']['base']['lic_yr'])}")
    print(f"Proof of concept (2 engineers x 2 weeks, base rate): {k(r['_poc_base'])}")


if __name__ == "__main__":
    import sys
    r = run()
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1, default=lambda x: round(x, 2)))
    else:
        report(r)
