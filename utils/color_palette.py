"""Color palette module for cargo color customization"""

from typing import Dict, List, Optional, Tuple


# Color palette definition: 6 main colors, each with 5 tones (from main to light)
COLOR_PALETTE: Dict[str, Dict[str, List[str]]] = {
    "red": {
        "name": "Kırmızı",
        "tons": ["#CC0000", "#FF1A21", "#FF4D54", "#FF8087", "#FFB3BA"]  # Ana → Açık
    },
    "blue": {
        "name": "Mavi",
        "tons": ["#0066CC", "#1A8CFF", "#4DA6FF", "#80C0FF", "#B3D9FF"]
    },
    "dark_gray": {
        "name": "Koyu Gri",
        "tons": ["#2C2C2C", "#555555", "#808080", "#A9A9A9", "#D3D3D3"]
    },
    "green": {
        "name": "Yeşil",
        "tons": ["#00CC00", "#1AFF1A", "#4DFF4D", "#80FF80", "#B3FFB3"]
    },
    "orange": {
        "name": "Turuncu",
        "tons": ["#CC6600", "#FF8C1A", "#FFA64D", "#FFC080", "#FFD9B3"]
    },
    "yellow": {
        "name": "Sarı",
        "tons": ["#CCCC00", "#FFFF1A", "#FFFF4D", "#FFFF80", "#FFFFB3"]
    }
}


def get_color_name(color_key: str) -> str:
    """Get Turkish name for a color key
    
    Args:
        color_key: Color key (e.g., "red", "blue")
        
    Returns:
        Turkish color name
    """
    return COLOR_PALETTE.get(color_key, {}).get("name", color_key)


def get_color_tones(color_key: str) -> List[str]:
    """Get all tones for a color
    
    Args:
        color_key: Color key (e.g., "red", "blue")
        
    Returns:
        List of hex color codes (from main to light)
    """
    return COLOR_PALETTE.get(color_key, {}).get("tons", [])


def get_color_tone(color_key: str, tone_index: int) -> Optional[str]:
    """Get specific tone for a color
    
    Args:
        color_key: Color key (e.g., "red", "blue")
        tone_index: Tone index (0-4, where 0 is main color, 4 is lightest)
        
    Returns:
        Hex color code or None if invalid
    """
    tones = get_color_tones(color_key)
    if 0 <= tone_index < len(tones):
        return tones[tone_index]
    return None


def get_main_color(color_key: str) -> Optional[str]:
    """Get main (darkest) tone for a color
    
    Args:
        color_key: Color key (e.g., "red", "blue")
        
    Returns:
        Hex color code of main tone or None if invalid
    """
    return get_color_tone(color_key, 0)


def get_all_color_keys() -> List[str]:
    """Get all available color keys
    
    Returns:
        List of color keys
    """
    return list(COLOR_PALETTE.keys())


def find_color_for_hex(hex_color: str) -> Optional[Tuple[str, int]]:
    """Find color key and tone index for a given hex color
    
    Args:
        hex_color: Hex color code (e.g., "#FF4D54")
        
    Returns:
        Tuple of (color_key, tone_index) or None if not found
    """
    hex_color = hex_color.upper()
    for color_key, color_data in COLOR_PALETTE.items():
        for tone_index, tone_hex in enumerate(color_data["tons"]):
            if tone_hex.upper() == hex_color:
                return (color_key, tone_index)
    return None


def is_valid_custom_color(hex_color: str) -> bool:
    """Check if a hex color is in the palette
    
    Args:
        hex_color: Hex color code
        
    Returns:
        True if color is in palette, False otherwise
    """
    return find_color_for_hex(hex_color) is not None

