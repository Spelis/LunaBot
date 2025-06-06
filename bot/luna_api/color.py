from enum import IntEnum


class CatppuccinColors(IntEnum):
    ROSEWATER = 0xF5E0DC
    FLAMINGO = 0xF2CDCD
    PINK = 0xF5C2E7
    MAUVE = 0xCBA6F7
    RED = 0xF38BA8
    MAROON = 0xEBA0AC
    PEACH = 0xFAB387
    YELLOW = 0xF9E2AF
    GREEN = 0xA6E3A1
    TEAL = 0x94E2D5
    SKY = 0x89DCEB
    SAPPHIRE = 0x74C7EC
    BLUE = 0x89B4FA
    LAVENDER = 0xB4BEFE
    TEXT = 0xCDD6F4
    BASE = 0x1E1E2E
    MANTLE = 0x181825
    CRUST = 0x11111B


class LunaColors(IntEnum):
    PRIMARY = CatppuccinColors.MAUVE.value
    SECONDARY = PRIMARY  # No way that's valid
    ERROR = CatppuccinColors.RED.value
    SUCCESS = CatppuccinColors.GREEN.value
