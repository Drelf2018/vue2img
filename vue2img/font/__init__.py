import os

FONTPATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "HarmonyOS_Sans_SC_Medium.ttf"
    )
)

def FontWeight(size: str) -> str:
    return FONTPATH.replace("Medium", size)