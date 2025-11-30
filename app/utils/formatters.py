def format_price(price):
    """
    Format price with dot separators (e.g., 10.000.0, 45.000.0)
    """
    # Convert to string and handle decimal places
    price_str = f"{price:.1f}"
    integer_part, decimal_part = price_str.split(".")
    
    # Add dot separators to integer part (from right to left)
    formatted_integer = ""
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            formatted_integer = "." + formatted_integer
        formatted_integer = digit + formatted_integer
    
    return f"{formatted_integer}.{decimal_part}"
