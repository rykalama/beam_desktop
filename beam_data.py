"""Built-in material and section properties for Beam Designer."""

STEEL_SECTIONS = {
    "W8x10": {"ix": 30.8, "sx": 7.81, "weight": 10.0},
    "W10x12": {"ix": 53.8, "sx": 10.9, "weight": 12.0},
    "W12x26": {"ix": 204.0, "sx": 33.4, "weight": 26.0},
    "W14x22": {"ix": 199.0, "sx": 29.0, "weight": 22.0},
    "W16x26": {"ix": 301.0, "sx": 38.4, "weight": 26.0},
    "W18x35": {"ix": 510.0, "sx": 57.6, "weight": 35.0},
    "W21x44": {"ix": 843.0, "sx": 81.6, "weight": 44.0},
    "W24x55": {"ix": 1350.0, "sx": 114.0, "weight": 55.0},
}

LUMBER_SECTIONS = {
    "2x8": {"ix": 47.63, "sx": 13.14},
    "2x10": {"ix": 98.93, "sx": 21.39},
    "2x12": {"ix": 177.98, "sx": 31.64},
}

MATERIALS = {
    "Steel": {"E": 29000.0, "fb_allow": 30.0, "sections": STEEL_SECTIONS},
    "Lumber": {"E": 1600.0, "fb_allow": 0.900, "sections": LUMBER_SECTIONS},
}


def section_properties(material: str, section: str) -> dict:
    """Return a complete copy of the selected section's properties."""
    properties = dict(MATERIALS[material]["sections"][section])
    properties.update({"E": MATERIALS[material]["E"], "fb_allow": MATERIALS[material]["fb_allow"]})
    return properties
