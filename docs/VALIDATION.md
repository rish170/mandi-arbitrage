# Mandi Arbitrage Accuracy Validation Report

This document records the empirical validation of the net profit calculation engine against manual field calculations across 10 real-world agricultural trading scenarios.

## How to Complete Manual Scenario Validation

To validate the engine against external ground truth:

1. Open `backend/data/validation/scenarios.csv`.
2. For each scenario row:

   - **`manual_price_q`**: Check the official published modal price on Agmarknet/eNAM or data.gov.in for that mandi.
   - **`manual_road_km`**: Measure driving distance in Google Maps from the origin pincode centroid to the target APMC Mandi.
   - **`manual_fee_pct` & `manual_commission_pct`**: Verify local APMC mandi cess (e.g. 1.0% cess, 2.0% commission agent charge).
   - **`manual_rate_per_km`**: Enter prevailing commercial transport freight rate for the vehicle type (e.g. ₹14/km tempo, ₹18/km pickup, ₹26/km mini truck, ₹38/km truck).
   - **`manual_net_q`**: Independently calculate net profit using a standard handheld calculator or spreadsheet:
     $$\text{Realized} = \text{Price} \times (1 - \text{QualityCut})$$
     $$\text{Fees} = \text{Realized} \times (\text{Fee} + \text{Commission})$$
     $$\text{Transport} = \frac{\lceil \text{Qty} / \text{Cap} \rceil \times \text{Rate} \times \text{Km}}{\text{Qty}}$$
     $$\text{Net} = \text{Realized} - \text{Fees} - \text{Transport} - \text{Other}$$
3. Re-run `python backend/scripts/validate_accuracy.py`.

## Validation Results (10 Scenarios)

| ID | Origin | Commodity | Quantity (q) | Vehicle | Grade | Mandi | Manual Price (₹/q) | Manual Road (km) | Manual Net (₹/q) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 440001 | Wheat | 10.0 | pickup | Good | APMC Nagpur | TBD | TBD | TBD |  |
| 2 | 440001 | Wheat | 15.0 | pickup | Average | APMC Wardha | TBD | TBD | TBD |  |
| 3 | 440001 | Soyabean | 8.0 | tempo | Good | APMC Nagpur | TBD | TBD | TBD |  |
| 4 | 444001 | Soyabean | 20.0 | mini_truck | Below average | APMC Akola | TBD | TBD | TBD |  |
| 5 | 444001 | Onion | 25.0 | mini_truck | Good | APMC Akola | TBD | TBD | TBD |  |
| 6 | 444001 | Wheat | 40.0 | mini_truck | Average | APMC Khamgaon | TBD | TBD | TBD |  |
| 7 | 414001 | Onion | 12.0 | pickup | Poor | APMC Karjat | TBD | TBD | TBD |  |
| 8 | 414001 | Tomato | 5.0 | tempo | Good | APMC Ahilyanagar | TBD | TBD | TBD |  |
| 9 | 414001 | Soyabean | 30.0 | mini_truck | Good | APMC Kopargaon | TBD | TBD | TBD |  |
| 10 | 414001 | Wheat | 60.0 | truck | Below average | APMC Ahilyanagar | TBD | TBD | TBD |  |

> [!NOTE]
> Awaiting completion of manual columns in `backend/data/validation/scenarios.csv`.

## Methodology Description

The Mandi Arbitrage Advisor net profit calculation engine evaluates candidate mandis using a multi-step financial realization formula:
1. **Gross Price Base**: Fetches latest modal mandi prices recorded in the daily snapshot pipeline within a 3-day freshness window.
2. **Quality Discount**: Applies grade-specific physical auction cuts (Good 0%, Average 5%, Below Average 10%, Poor 15%).
3. **APMC Statutory Deductions**: Deducts local market cess and commission agent percentages from the quality-adjusted realized price.
4. **Freight Logistics**: Models non-linear discrete vehicle capacities using ceiling division (e.g. 10 quintals on an 8 quintal tempo requires 2 vehicles), multiplied by distance and rate per km.
5. **Net Realization**: Subtracts transport and optional handling charges from the net mandi realization.

## Known Sources of Error

1. **Price Timing & Snapshot Lag**: APMC physical auction rates fluctuate throughout the trading day. data.gov.in publishes single daily modal prices which may reflect a 12-24 hour delay relative to live spot bidding.
2. **Route Choice & Road Geometry**: Real vehicular navigation can deviate from straight-line haversine * 1.3 approximations or Google Routes API recommendations depending on rural road conditions, seasonal monsoon detours, and toll bypasses.
3. **Arithmetic Rounding**: Handheld calculators frequently round intermediate products (such as transport cost per quintal) to 2 decimal places, whereas the engine maintains full Python Decimal precision throughout intermediate steps and quantizes strictly at the final output boundary.