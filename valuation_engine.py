def calculate_valuation(
    asking_price: int, 
    condition_score: int, 
    land_value: int, 
    bedrooms: int = 0, 
    bathrooms: int = 0, 
    carspaces: int = 0
) -> dict:
    """
    Calculates the intrinsic value of a property and determines the Hype Premium.
    Now includes dynamic hardware pricing based on Sydney construction baselines!
    """
    # Safety fallback if data is missing
    if asking_price <= 0 or land_value <= 0:
        return {
            "intrinsic_value": 0,
            "house_value": 0,
            "land_to_asset_ratio": 0.0,
            "hype_premium": 0,
            "is_overpriced": False,
            "error": "Invalid pricing data"
        }

    # Handle N/A or failed AI scores by assuming an average condition of 5
    if not isinstance(condition_score, int):
        try:
            condition_score = int(condition_score)
        except (ValueError, TypeError):
            condition_score = 5

    # --- DYNAMIC HARDWARE VALUATION ---
    # If the API found beds/baths, we calculate the exact replacement cost
    if bedrooms > 0 or bathrooms > 0:
        base_shell_cost = 200000
        bed_cost = bedrooms * 75000
        bath_cost = bathrooms * 40000
        car_cost = carspaces * 25000
        max_build_cost = base_shell_cost + bed_cost + bath_cost + car_cost
    else:
        # Fallback if the Domain API didn't have room data
        max_build_cost = 600000 

    # Apply the AI Depreciation (Condition Score / 10)
    ai_adjusted_house_value = int((condition_score / 10.0) * max_build_cost)

    # Calculate Total Intrinsic Value (Dirt + Hardware)
    intrinsic_value = land_value + ai_adjusted_house_value

    # Calculate Land-to-Asset Ratio
    land_to_asset_ratio = round((land_value / asking_price) * 100, 1)

    # Calculate Hype Premium
    hype_premium = asking_price - intrinsic_value
    is_overpriced = hype_premium > 0

    return {
        "intrinsic_value": intrinsic_value,
        "house_value": ai_adjusted_house_value,
        "land_to_asset_ratio": land_to_asset_ratio,
        "hype_premium": hype_premium,
        "is_overpriced": is_overpriced,
        "error": None
    }
