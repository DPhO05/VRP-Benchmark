# Team-3 solver condition analysis

## Winners by time_limit
- `4.0`: `Greedy_LocalSearch_CPP` is practical winner in 6/10 condition groups.

## Winners by size_group
- `large`: `Greedy_LocalSearch_CPP` is practical winner in 2/2 condition groups.
- `medium`: `Greedy_SA` is practical winner in 1/1 condition groups.
- `stress`: `Greedy_LocalSearch_CPP` is practical winner in 3/5 condition groups.
- `tiny`: `Greedy_SA` is practical winner in 1/2 condition groups.

## Winners by distribution
- `sample`: `Greedy_LocalSearch_CPP` is practical winner in 6/10 condition groups.

Interpretation notes:
- MIP is only included for `N <= 35`; it is useful as a small-instance optimal/near-optimal reference, not as the main large-N solver.
- `Greedy_LocalSearch_CPP` is expected to dominate runtime on larger cases because it is compiled and has cheaper local-search loops.
- `Greedy_RL` can be competitive when extra time helps assignment rebalancing, but Python overhead is visible at short limits.
