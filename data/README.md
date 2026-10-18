Reference dataset (8 labeled classes, 15 trials each, ~20 Hz) from the drill press case study — ready to experiment with out of the box

## Case Study: Vertical Drill Press

To validate the pipeline end-to-end, it was deployed on a vertical drill
press to classify **drill bit condition** in real time from sensor data
alone — no manual inspection required.

**Eight condition classes** were defined along three axes: bit quality
(good/poor), alignment (aligned/misaligned), and physical state
(normal/flattened/broken). Each class maps to a health score (0–100) and a
maintenance recommendation:

| # | Class | Health Score | Maintenance Action |
|---|-------|:---:|---|
| 1 | good_aligned | 100 | Healthy Operation |
| 2 | good_misaligned | 85 | Inspect Alignment |
| 3 | good_flattened | 70 | Schedule Replacement |
| 4 | poor_aligned | 60 | Monitor Closely |
| 5 | poor_misaligned | 45 | Inspect Alignment (urgent) |
| 6 | good_broken | 30 | Replace Immediately |
| 7 | poor_flattened | 20 | Schedule Replacement (imminent) |
| 8 | poor_broken | 0 | Replace Immediately (critical) |

This class taxonomy, sensor set, and health-score mapping are **specific to
the drill press demo** — see [Adapting This Pipeline](#adapting-this-pipeline-to-your-own-machine)
for how to define your own classes and health scores for a different
machine.
