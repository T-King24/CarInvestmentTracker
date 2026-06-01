from __future__ import annotations

# Brand accent themes used by the UI. When a make is selected the frontend
# applies the matching palette (subtle gradient + accent) so, e.g., Ferrari turns
# the page red and Lamborghini turns it yellow. Colours are chosen to stay
# readable against the dark UI (the frontend keeps light text on dark panels).
BRAND_THEMES: dict[str, dict[str, str]] = {
    "Ferrari": {"accent": "#ff2800", "accent2": "#b71c1c", "tint": "rgba(255, 40, 0, 0.16)"},
    "Lamborghini": {"accent": "#ffcc00", "accent2": "#caa200", "tint": "rgba(255, 204, 0, 0.16)"},
    "Porsche": {"accent": "#c9a227", "accent2": "#9c7b18", "tint": "rgba(201, 162, 39, 0.16)"},
    "BMW": {"accent": "#3aa0ff", "accent2": "#1c69d4", "tint": "rgba(58, 160, 255, 0.16)"},
    "Mercedes-Benz": {"accent": "#9fb4c7", "accent2": "#6c7c8c", "tint": "rgba(159, 180, 199, 0.16)"},
    "Aston Martin": {"accent": "#1f7a5a", "accent2": "#0f5740", "tint": "rgba(31, 122, 90, 0.18)"},
    "Jaguar": {"accent": "#2e7d32", "accent2": "#1b5e20", "tint": "rgba(46, 125, 50, 0.18)"},
    "Land Rover": {"accent": "#4f7d4f", "accent2": "#2f5d2f", "tint": "rgba(79, 125, 79, 0.18)"},
    "Audi": {"accent": "#e34234", "accent2": "#a51b16", "tint": "rgba(227, 66, 52, 0.16)"},
    "McLaren": {"accent": "#ff7a00", "accent2": "#cc5f00", "tint": "rgba(255, 122, 0, 0.16)"},
    "Lotus": {"accent": "#ffdf00", "accent2": "#1f6f43", "tint": "rgba(255, 223, 0, 0.16)"},
    "Toyota": {"accent": "#eb0a1e", "accent2": "#b00816", "tint": "rgba(235, 10, 30, 0.16)"},
    "Nissan": {"accent": "#c3002f", "accent2": "#8c0022", "tint": "rgba(195, 0, 47, 0.16)"},
    "Honda": {"accent": "#e60012", "accent2": "#b0000e", "tint": "rgba(230, 0, 18, 0.16)"},
}

# Neutral default palette (matches the base UI accent) for unknown makes.
DEFAULT_THEME = {"accent": "#f5a524", "accent2": "#e0791a", "tint": "rgba(245, 165, 36, 0.14)"}


def get_brand_theme(make: str) -> dict[str, str]:
    key = next((k for k in BRAND_THEMES if k.lower() == (make or "").lower()), None)
    return BRAND_THEMES[key] if key else DEFAULT_THEME


def get_all_brand_themes() -> dict[str, dict[str, str]]:
    return {**BRAND_THEMES, "_default": DEFAULT_THEME}
