# Team-3 solver condition analysis

## Winners by time_limit
- `2.0`: `Greedy_LocalSearch_CPP` is practical winner in 54/70 condition groups.

## Winners by size_group
- `small`: `Greedy_LocalSearch_CPP` is practical winner in 21/28 condition groups.
- `tiny`: `Greedy_LocalSearch_CPP` is practical winner in 33/42 condition groups.

## Winners by distribution
- `adversarial`: `Greedy_LocalSearch_CPP` is practical winner in 8/10 condition groups.
- `cluster`: `Greedy_LocalSearch_CPP` is practical winner in 9/10 condition groups.
- `grid`: `Greedy_LocalSearch_CPP` is practical winner in 8/10 condition groups.
- `line`: `SA_Algo` is practical winner in 6/10 condition groups.
- `outlier`: `Greedy_LocalSearch_CPP` is practical winner in 6/10 condition groups.
- `ring`: `Greedy_LocalSearch_CPP` is practical winner in 9/10 condition groups.
- `uniform`: `Greedy_LocalSearch_CPP` is practical winner in 10/10 condition groups.

Interpretation notes:
- MIP is only included for `N <= 35`; it is useful as a small-instance optimal/near-optimal reference, not as the main large-N solver.
- `Greedy_LocalSearch_CPP` is expected to dominate runtime on larger cases because it is compiled and has cheaper local-search loops.
- `Greedy_RL` can be competitive when extra time helps assignment rebalancing, but Python overhead is visible at short limits.
