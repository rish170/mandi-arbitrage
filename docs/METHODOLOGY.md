# Mandi Arbitrage Methodology & Net Profit Formula

This document serves as the single source of truth for the Mandi Arbitrage Advisor financial and logistical calculations.

---

## 1. The Core Problem
Indian agricultural producers often sell their harvest at the nearest local APMC (Agricultural Produce Market Committee) mandi. However, mandi prices vary significantly across districts and states. Selling at a distant mandi with a higher price is only beneficial if the net realization per quintal exceeds the additional transport costs, statutory APMC market fees, commission agent charges, and produce quality discounts.

Most existing market dashboards (e.g. eNAM) only report gross modal prices, omitting:
1. Transport cost scaling with vehicle size and road distance
2. Quality deductions applied during physical mandi auctioning
3. Mandatory market fees and intermediary commissions
4. Incidental handling charges (loading, unloading, weighing)

---

## 2. Mathematical Formulation

### Inputs
- $\text{price\_basis}$: Chosen price point (`modal` [default], `min`, or `max`) in ₹/quintal.
- $\text{quality\_cut\_pct}$: Produce quality discount percentage (0% to 30%).
- $\text{quantity\_q}$: Produce quantity in quintals ($Q$).
- $\text{vehicle}$: Vehicle specification containing capacity ($C_v$) in quintals and standard freight rate ($R_v$) in ₹/km.
- $\text{market\_fee\_pct}$: APMC statutory market cess percentage.
- $\text{commission\_pct}$: Commission agent percentage.
- $\text{road\_km}$: Actual road distance in kilometers.
- $\text{round\_trip\_factor}$: Empty return trip multiplier (default 1.0).
- $\text{include\_other\_charges}$: Boolean toggle for miscellaneous mandi charges.
- $\text{loading\_unloading\_q}$: Handling charge in ₹/quintal (default ₹3/q).
- $\text{weighing\_q}$: Weighment charge in ₹/quintal (default ₹1/q).

---

### Step-by-Step Formula

$$\text{price\_q} = \text{Mandi price for selected basis (within past 3 days)}$$

$$\text{quality\_cut\_q} = \frac{\text{price\_q} \times \text{quality\_cut\_pct}}{100}$$

$$\text{realized\_q} = \text{price\_q} - \text{quality\_cut\_q}$$

$$\text{mandi\_fee\_q} = \frac{\text{realized\_q} \times (\text{market\_fee\_pct} + \text{commission\_pct})}{100}$$

$$\text{vehicles\_needed} = \left\lceil \frac{\text{quantity\_q}}{C_v} \right\rceil$$

$$\text{transport\_total} = \text{vehicles\_needed} \times R_v \times \text{road\_km} \times \text{round\_trip\_factor}$$

$$\text{transport\_q} = \frac{\text{transport\_total}}{\text{quantity\_q}}$$

$$\text{other\_q} = \begin{cases} \text{loading\_unloading\_q} + \text{weighing\_q}, & \text{if } \text{include\_other\_charges} \\ 0, & \text{otherwise} \end{cases}$$

$$\text{net\_q} = \text{realized\_q} - \text{mandi\_fee\_q} - \text{transport\_q} - \text{other\_q}$$

$$\text{net\_total} = \text{net\_q} \times \text{quantity\_q}$$

$$\Delta_{\text{vs\_nearest\_q}} = \text{net\_q}(\text{mandi}) - \text{net\_q}(\text{nearest mandi by road distance})$$

---

## 3. Tie-Breaking and Ranking
- Mandis are ranked strictly by $\text{net\_q}$ in descending order.
- In the event of a tie in $\text{net\_q}$, the mandi with the smaller $\text{road\_km}$ is ranked higher.

---

## 4. Arithmetic Precision Standards
All financial calculations use Python's arbitrary-precision `Decimal` type. Standard IEEE 754 floats are forbidden in calculation logic to eliminate floating-point representation drift. Output rounding occurs strictly at serialization to 2 decimal places.
