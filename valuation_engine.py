from __future__ import annotations


def calculate_statutory_land_value(land_size_sqm: float, council_land_rate_per_sqm: float) -> float:
    """Calculate statutory land value from land size and council land rate."""
    return land_size_sqm * council_land_rate_per_sqm


def calculate_true_market_land_value(statutory_land_value: float, local_market_multiplier: float) -> float:
    """Calculate true market land value using a local market multiplier."""
    return statutory_land_value * local_market_multiplier


def calculate_base_building_cost(building_size_sqm: float, construction_rate_per_sqm: float) -> float:
    """Calculate base replacement cost of the building."""
    return building_size_sqm * construction_rate_per_sqm


def calculate_depreciated_building_value(
    base_building_cost: float, effective_age_years: float, lifespan_years: float
) -> float:
    """Calculate depreciated building value with linear depreciation and a 0 floor."""
    depreciation_ratio: float = effective_age_years / lifespan_years
    depreciation_ratio = max(0.0, min(1.0, depreciation_ratio))
    return base_building_cost * (1.0 - depreciation_ratio)


def calculate_intrinsic_value(true_market_land_value: float, depreciated_building_value: float) -> float:
    """Calculate intrinsic value as land value plus depreciated building value."""
    return true_market_land_value + depreciated_building_value


def calculate_hype_premium(asking_price: float, intrinsic_value: float) -> float:
    """Calculate hype premium: market asking price minus intrinsic value."""
    return asking_price - intrinsic_value


def calculate_lar(true_market_land_value: float, asking_price: float) -> float:
    """Calculate Land-to-Asset Ratio (LAR) as a percentage."""
    return (true_market_land_value / asking_price) * 100.0


def main() -> None:
    # Dummy example inputs
    asking_price: float = 1_500_000.0
    land_size_sqm: float = 600.0
    building_size_sqm: float = 200.0
    effective_age_years: float = 20.0
    local_market_multiplier: float = 1.35

    # Assumed rates for demonstration
    council_land_rate_per_sqm: float = 1_000.0
    construction_rate_per_sqm: float = 3_000.0
    lifespan_years: float = 60.0

    statutory_land_value: float = calculate_statutory_land_value(land_size_sqm, council_land_rate_per_sqm)
    true_market_land_value: float = calculate_true_market_land_value(
        statutory_land_value, local_market_multiplier
    )
    base_building_cost: float = calculate_base_building_cost(building_size_sqm, construction_rate_per_sqm)
    depreciated_building_value: float = calculate_depreciated_building_value(
        base_building_cost, effective_age_years, lifespan_years
    )
    intrinsic_value: float = calculate_intrinsic_value(true_market_land_value, depreciated_building_value)
    hype_premium: float = calculate_hype_premium(asking_price, intrinsic_value)
    lar_percentage: float = calculate_lar(true_market_land_value, asking_price)

    print("=== Hype vs. Hardware Valuation ===")
    print(f"Asking Price: ${asking_price:,.2f}")
    print(f"Statutory Land Value: ${statutory_land_value:,.2f}")
    print(f"True Market Land Value: ${true_market_land_value:,.2f}")
    print(f"Depreciated Building Value: ${depreciated_building_value:,.2f}")
    print(f"Intrinsic Value: ${intrinsic_value:,.2f}")
    print(f"Hype Premium: ${hype_premium:,.2f}")
    print(f"LAR: {lar_percentage:.2f}%")


if __name__ == "__main__":
    main()
