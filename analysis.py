"""Rebuild the OR498 rankings from the raw scores and weights in data/.

Run:  pip install -r requirements.txt  then  python analysis.py
Scores are 1 to 10 favourability ratings (higher is better for every criterion,
including cost-type ones, as in the report). Weights are the report's published values.
"""
import numpy as np
import pandas as pd

RNG_SEED = 2030          # fixed so the Monte Carlo results are reproducible
N_RUNS = 4000            # random weight perturbations
SPREAD = 0.30            # each group weight is scaled by a factor in [1 - SPREAD, 1 + SPREAD]

scores = pd.read_csv("data/decision_scores.csv")
weights = pd.read_csv("data/weights.csv")
pair = pd.read_csv("data/pairwise_core.csv", index_col=0)
reported = pd.read_csv("data/reported_ranks.csv").set_index("project")
X = scores.drop(columns=["project", "name"]).to_numpy(float)

def topsis(w):
    V = X / np.sqrt((X ** 2).sum(0)) * w
    best, worst = V.max(0), V.min(0)
    d_pos = np.sqrt(((V - best) ** 2).sum(1))
    d_neg = np.sqrt(((V - worst) ** 2).sum(1))
    return d_neg / (d_pos + d_neg)                    # closeness Ci, higher is better

def vikor(w, v=0.5):
    N = w * (X.max(0) - X) / (X.max(0) - X.min(0))
    S, R = N.sum(1), N.max(1)
    return v * (S - S.min()) / (S.max() - S.min()) + (1 - v) * (R - R.min()) / (R.max() - R.min())

rank = lambda a, desc: pd.Series(a).rank(ascending=not desc, method="min").astype(int).to_numpy()

# AHP: weights of the five criteria from the pairwise matrix
P = pair.to_numpy(float)
w5 = (P / P.sum(0)).mean(1)
lam = (P @ w5 / w5).mean()
CI = (lam - 5) / 4
print(f"Core AHP weights {np.round(w5, 4)}  lambda_max {lam:.4f}  CR {CI / 1.12:.4f}\n")

R = {}
for name, col in (("AHP", "AHP"), ("FAHP", "FuzzyAHP"), ("BWM", "BWM")):
    w = weights[col].to_numpy(float)
    R["T_" + name] = rank(topsis(w), True)
    R["V_" + name] = rank(vikor(w), False)
out = pd.DataFrame(R, index=scores.project)
out["average_rank"] = out.mean(axis=1).round(2)
out["final_rank"] = rank(out.average_rank.to_numpy(), False)
same = (out[reported.columns] == reported.loc[out.index]).all(axis=1)
out["matches_report"] = same.map({True: "PASS", False: "FAIL"})
print(out.join(scores.set_index("project").name).to_string())
print(f"\n{same.sum()} of {len(out)} projects reproduce the report's ranks exactly.")

assert same.all(), "Rebuilt ranks no longer match the report"

# ---------------------------------------------------------------------------
# Robustness checks (mirrors the Robustness tab in index.html)
# ---------------------------------------------------------------------------
print("\n=== 1. Rank agreement between the six scenarios (Kendall tau-b) ===")
def kendall_tau_b(a, b):
    c = d = ta = tb = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            x, y = np.sign(a[i] - a[j]), np.sign(b[i] - b[j])
            if x and y:
                c, d = (c + 1, d) if x == y else (c, d + 1)
            else:
                ta += (x == 0)
                tb += (y == 0)
    n0 = c + d
    return (c - d) / np.sqrt((n0 + ta) * (n0 + tb))

cols = list(R)
tau = pd.DataFrame([[kendall_tau_b(out[a].to_numpy(), out[b].to_numpy()) for b in cols] for a in cols],
                   index=cols, columns=cols)
print(tau.round(2).to_string())

print(f"\n=== 2. Monte Carlo weight sensitivity ({N_RUNS} runs, group weights x U[{1-SPREAD:.2f}, {1+SPREAD:.2f}]) ===")
groups = np.array([int(c[1]) - 1 for c in scores.columns[2:]])        # C11 -> group 0, C21 -> group 1, ...
w_base = weights["AHP"].to_numpy(float)
local = w_base / w5[groups]
rng = np.random.default_rng(RNG_SEED)
counts = {m: np.zeros((len(X), len(X))) for m in ("TOPSIS", "VIKOR")}
for _ in range(N_RUNS):
    g = w5 * rng.uniform(1 - SPREAD, 1 + SPREAD, 5)
    w = (g / g.sum())[groups] * local
    for m, r in (("TOPSIS", rank(topsis(w), True)), ("VIKOR", rank(vikor(w), False))):
        counts[m][np.arange(len(X)), r - 1] += 1
names = scores.set_index("project").name
for m, c in counts.items():
    p = c / N_RUNS
    t = pd.DataFrame({"project": names.values, "P(first)": p[:, 0], "P(top 3)": p[:, :3].sum(1),
                      "P(last)": p[:, -1], "mean_rank": p @ np.arange(1, len(X) + 1)}).sort_values("mean_rank")
    print(f"\n{m}\n" + t.round(3).to_string(index=False))

print("\n=== 3. VIKOR validity conditions (C1 acceptable advantage, C2 acceptable stability) ===")
DQ = 1 / (len(X) - 1)
for name, col in (("AHP", "AHP"), ("FuzzyAHP", "FuzzyAHP"), ("BWM", "BWM")):
    w = weights[col].to_numpy(float)
    N = w * (X.max(0) - X) / (X.max(0) - X.min(0))
    S, Rr, Q = N.sum(1), N.max(1), vikor(w)
    order = np.argsort(Q)
    a1, a2 = order[0], order[1]
    c1 = Q[a2] - Q[a1] >= DQ
    c2 = S.argmin() == a1 or Rr.argmin() == a1
    comp = [a1, a2] if not c2 else ([i for i in order if Q[i] - Q[a1] < DQ] if not c1 else [a1])
    print(f"{name:9s} best={names.iloc[a1]:<20s} gap={Q[a2]-Q[a1]:.3f} (need {DQ:.3f}) "
          f"C1={'pass' if c1 else 'FAIL'} C2={'pass' if c2 else 'FAIL'} -> {', '.join(names.iloc[comp])}")

print("\n=== 4. VIKOR ranks for different v (AHP weights) ===")
vt = pd.DataFrame({f"v={v}": rank(vikor(weights["AHP"].to_numpy(float), v), False) for v in (0.25, 0.5, 0.75)},
                  index=names.values)
print(vt.to_string())
