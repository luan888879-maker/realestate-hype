# Product Specification: "Hype vs. Hardware" Real Estate Valuation MVP

## Core Objective
Build a Python-based valuation engine that calculates the Intrinsic Value of a property by separating the appreciating asset (Land) from the depreciating asset (Building), calculating the "Hype Premium" (Market Price vs Intrinsic Value), and the Land-to-Asset Ratio (LAR).

## Core Formulas
1.  **Statutory Land Value** = Land Size (sqm) * Council Land Rate ($/sqm)
2.  **True Market Land Value** = Statutory Land Value * Local Market Multiplier (e.g., 1.35)
3.  **Base Building Cost** = Building Size (sqm) * Construction Rate ($/sqm)
4.  **Depreciated Building Value** = Base Building Cost * (1 - (Effective Age / Lifespan))
5.  **Intrinsic Value** = True Market Land Value + Depreciated Building Value
6.  **Hype Premium** = Asking Price - Intrinsic Value
7.  **Land-to-Asset Ratio (LAR)** = (True Market Land Value / Asking Price) * 100

## Engineering Constraints
- Write clean, modular Python code.
- Use explicit type hinting for all function parameters and return values.
- Do not add any external API calls or UI elements yet. Focus strictly on the mathematical logic.