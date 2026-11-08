# Prioritizing Saudi Vision 2030 projects with fuzzy multi-criteria decision making

Which Vision 2030 projects should come first? A fuzzy multi-criteria evaluation of 12 projects on 19 criteria, with a live dashboard and a reproducible Python analysis.
An interactive dashboard and reproducible analysis for a research report that ranks 12 Saudi giga- and infrastructure projects on 19 sub-criteria in five groups (financial viability, market potential, risk, strategic fit, implementation readiness).

**Open it:** download `index.html` and double-click it. No install, works offline.

## Methods
- **Weighting:** AHP, Fuzzy AHP (Buckley geometric mean) and Best-Worst Method (BWM).
- **Ranking:** TOPSIS and VIKOR, each run with all three weightings, giving six scenarios.
- **Checks:** AHP consistency ratios, rank agreement across scenarios (Kendall τ-b), one-at-a-time weight sensitivity, a 4,000-run Monte Carlo weight perturbation, VIKOR validity conditions (C1 and C2), and sensitivity to the VIKOR parameter v.

## Findings
- **Rua Al Madinah** ranks first on average (average rank 1.5), followed by **Ras Al Khair 2 Desalination** and **ROSHN - Sedra**. **NEOM** ranks last in all six scenarios.
- Risk carries the largest weight (41% under AHP) under every weighting method.
- TOPSIS and VIKOR disagree most about Ras Al Khair 2 (first under TOPSIS, fourth under VIKOR) and the King Salman Energy Park (third under TOPSIS, sixth to eighth under VIKOR).
- Changing the weight of the financial or risk group by 20% moves several projects' ranks; the market and readiness groups barely matter.
- Under random ±30% weight changes, NEOM is last in every run, Rua Al Madinah is in the top 3 in every run, and VIKOR ranks Rua Al Madinah first every time. TOPSIS ranks Ras Al Khair 2 first in 93% of runs.
- VIKOR's acceptable-advantage condition (C1) fails for all three weightings (gap to second place ≈ 0.02, needed 0.09), so VIKOR supports a compromise set (Rua Al Madinah and ROSHN - Sedra) rather than a single winner.
- The choice of ranker matters more than the choice of weighting method: Kendall τ is at least 0.85 across weightings within a ranker, but only 0.67 to 0.82 between TOPSIS and VIKOR.

## Dashboard tabs
| Tab | Content |
|---|---|
| Overview | Final ranking across six scenarios, showing where TOPSIS and VIKOR disagree |
| Criteria weights | Group and sub-criteria weights for the three methods, AHP consistency checks |
| Rankings | Rank heatmap for all scenarios and a live weight-sensitivity table |
| Simulator | Sliders for the five group weights that re-rank the projects instantly |
| Calculations | AHP weights from the pairwise matrix and a step-by-step TOPSIS and VIKOR example for any project |
| Robustness | Monte Carlo weight sensitivity, Kendall τ agreement matrix, VIKOR validity conditions, sensitivity to v |
| Process | How it was built, 14 validation checks against the report, data tables, assumptions |

## Excel workbook
`Abdullah_Alwahaibi_OR498_Excel.xlsx` rebuilds the weights and rankings with live Excel formulas (16 sheets: raw scores, AHP for the main criteria and each group, Fuzzy AHP, BWM, TOPSIS, VIKOR, six-scenario summary, sensitivity). Blue text is original input, black text is a formula, and yellow cells are key results. Labels in the workbook are in Arabic.

## Reproduce
```
pip install -r requirements.txt
python analysis.py
```
`analysis.py` rebuilds the AHP weights, TOPSIS and VIKOR from `data/`, asserts that all 12 projects get the same ranks as the report, then runs the robustness checks above (fixed random seed, so results are reproducible).

## Assumptions
- The 1 to 10 scores are the report's own expert ratings; this project does not re-estimate them.
- Every criterion, including cost-type ones, is scored so that higher is better. The report's rankings only reproduce under that treatment.
- Fuzzy AHP and BWM weights are the report's published values. AHP was rebuilt from its pairwise matrix; the other two were not re-derived.
- VIKOR uses v = 0.5 in the main analysis; the Robustness tab tests 0.25 and 0.75.
- Robustness tests perturb only the criteria weights. The expert scores are held fixed, so their subjectivity is not tested.
