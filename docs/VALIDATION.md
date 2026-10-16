# Mandi Arbitrage Validation Suite

## Objective
To ensure that engine outputs are within **5% of manual calculations** across 10 distinct, verified real-world scenarios.

---

## Validation Scenarios (10 Scenarios)
1. **Scenario 1**: Standard Wheat harvest in Nashik (tempo, Good quality, default APMC fees)
2. **Scenario 2**: Onion bulk transport from Lasalgaon to Pune (truck, Average quality)
3. **Scenario 3**: Soyabean smallholder in Latur (pickup, 5q quantity, round-trip factor)
4. **Scenario 4**: Cotton harvest in Jalgaon (mini-truck, customized fee override)
5. **Scenario 5**: Tomato perishable batch in Narayangaon (pickup, 10% quality cut)
6. **Scenario 6**: Potato transport with incidental handling charges enabled
7. **Scenario 7**: Paddy (Rice) multi-variety aggregation scenario
8. **Scenario 8**: Long distance trip triggering vehicle capacity ceiling
9. **Scenario 9**: Stale price boundary check (2-3 days age flag verification)
10. **Scenario 10**: Road distance fallback accuracy against Google Routes baseline

---

## Validation Test Execution
Test script: `backend/scripts/validate_accuracy.py`
Unit test runner: `pytest backend/tests/accuracy/test_scenarios.py`

*Detailed benchmark metrics and comparison tables will be generated during Phase 6.*
