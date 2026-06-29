"""Theme colors and shared constants."""

# Tokyo Night palette
BG_DARK = "#1a1b27"
BG_CARD = "#24283b"
BG_HIGHLIGHT = "#292e42"
BLUE = "#7aa2f7"
CYAN = "#7dcfff"
GREEN = "#9ece6a"
ORANGE = "#ff9e64"
PURPLE = "#bb9af7"
RED = "#f7768e"
YELLOW = "#e0af68"
TEXT = "#a9b1d6"
TEXT_DIM = "#8a94bd"
TEXT_BRIGHT = "#c0caf5"
BORDER = "#414868"

# --- Glass / elevation tokens (stored as hex + opacity; never rgba() in SVG fills) ---
# Deeper, cooler panel base so the white sheen reads as frosted glass.
SURFACE_BASE = "#1b1e2e"        # card panel base
SURFACE_RAISED = "#232843"      # inner tile base
GLASS_SHEEN_HEX = "#ffffff"
GLASS_SHEEN_TOP_OP = 0.07       # panel top sheen opacity
GLASS_TILE_TOP_OP = 0.06        # tile top sheen opacity
GLASS_TILE_SHADE_HEX = "#05060e"
GLASS_TILE_SHADE_OP = 0.18      # tile base darken for depth
GLASS_TOPHI_HEX = "#ffffff"
GLASS_TOPHI_OP = 0.16           # 1px top inner highlight
GLASS_HAIRLINE_HEX = "#c0caf5"  # TEXT_BRIGHT used at low alpha for borders
GLASS_HAIRLINE_OP = 0.14
GLASS_HAIRLINE_STRONG_OP = 0.22
GLASS_SHADOW_HEX = "#03040c"
GLASS_SHADOW_OP = 0.55
GLASS_INSET = 12                # shadow reservation band so blur never clips
GLASS_RX = 18                   # panel corner radius
GLASS_TILE_RX = 13              # inner tile corner radius

# Accent gradient stop pairs (for ribbons / sparklines / rings / progress)
GRAD_BLUE_CYAN = ("#7aa2f7", "#7dcfff")
GRAD_CYAN_MINT = ("#7dcfff", "#9ece6a")
GRAD_ORANGE_PINK = ("#ff9e64", "#f7768e")
GRAD_PURPLE_BLUE = ("#bb9af7", "#7aa2f7")

# --- Chart/status color tokens (single source; rendering code imports these,
#     never hard-codes hex — enforced by tests/test_design_contract.py) ---
SURFACE_BACKDROP = "#0c0e18"          # near-black card backdrop behind the frost
LANG_DEFAULT = "#8b8b8b"              # fallback language dot color
# Contribution-calendar intensity ramp (empty + levels 1..4)
CONTRIB_EMPTY = "#c0caf5"
CONTRIB_RAMP = ["#34528a", "#5b86d4", "#7dcfff", "#9ece6a"]
# Activity heatmap intensity ramp: (hex, fill_opacity) for empty + levels 1..4
HEATMAP_RAMP = [
    ("#c0caf5", 0.06),
    ("#35507a", 0.92),
    ("#4574b8", 0.96),
    ("#5ea6e8", 1.00),
    ("#7dcfff", 1.00),
]

# Language colors (GitHub Linguist palette)
LANG_COLORS = {
    "Python": "#3572A5",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "HTML": "#e34c26",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Go": "#00ADD8",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "C#": "#178600",
    "PHP": "#4F5D95",
    "Vue": "#41b883",
    "Shell": "#89e051",
    "C": "#555555",
    "Makefile": "#427819",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "CMake": "#DA3434",
    "Dockerfile": "#384d54",
    "GLSL": "#5686a5",
    "Batchfile": "#C1F12E",
    "Jupyter Notebook": "#DA5B0B",
}

# SVG dimensions
SVG_WIDTH = 840

# --- Type scale (DESIGN_SPEC Part 0): the ONLY allowed text sizes. Hierarchy is
#     expressed via this scale + weight, never via ad-hoc sizes. (size, weight) ---
TYPE_SCALE = {
    "display": (46, 600),    # the one PrimaryKpiCard value (Apple Semibold, not Bold)
    "metric_lg": (26, 600),  # secondary metric values
    "metric": (22, 600),     # compact metric values
    "title": (20, 600),      # section / hero titles
    "body": (14, 400),       # primary labels, row primary text
    "caption": (12, 400),    # secondary labels, timestamps
    "eyebrow": (11, 600),    # overlines (UPPERCASE, tracked)
    "chip": (11, 500),       # chip text
}
# Legibility floor for README SVGs downscaled into the column.
MIN_FONT_PX = 10

# Spacing scale (4px base) — gaps/pads resolve from here, not one-off literals.
SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}

# Fonts
FONT_MONO = "'Courier New', Courier, monospace"
FONT_SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

# GitHub username (sourced from unified settings)
from scripts.core.settings import Settings as _Settings  # noqa: E402

USERNAME = _Settings.from_env().username

# The profile repo itself (username/username) — excluded from "currently working"
# and activity feeds so the hourly auto-commit bot never appears as real work.
SELF_REPO = USERNAME

# Commit-message / actor markers produced by automation. These must never be
# surfaced as "currently working", "shipped", or activity.
BOT_COMMIT_MARKERS = (
    "update canonical profile artifacts",
    "update analytics & readme",
    "update badges from ci",
    "[skip ci]",
    "[ci skip]",
)
BOT_ACTOR_PREFIXES = ("github-actions",)

# Curated flagship repos for the spotlight (best work to showcase). This is the
# "showcase" set and is intentionally separate from the activity-driven
# "currently working" surface.
FEATURED_REPOS = [
    "ci-cd-hub",
    "voiceterm",
    "contact-suite-spring-react",
]

# RPG Game Card config
LEVEL_XP_BASE = 50  # XP needed for level 1
LEVEL_XP_SCALE = 1.5  # multiplier per level
