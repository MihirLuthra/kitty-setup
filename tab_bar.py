# pyright: reportMissingImports=false

from kitty.fast_data_types import Screen
from kitty.rgb import Color
from kitty.tab_bar import DrawData, ExtraData, TabBarData, as_rgb, draw_title
from kitty.utils import color_as_int


def _rgb(c: Color) -> int:
    return as_rgb(color_as_int(c))


# --- palette ---
WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)

TAB_BG_ACTIVE = WHITE
TAB_FG_ACTIVE = BLACK

TAB_BG_INACTIVE = Color(200, 200, 200)  # slightly off-white
TAB_FG_INACTIVE = Color(30, 30, 30)

EDGE_FG = Color(170, 170, 170)          # grey edges
BAR_BG = WHITE

# orange underline for active tab
UL_R, UL_G, UL_B = 255, 165, 0

SEP = "│"
PAD = "     "
ELL = "…"


def _draw_limited(screen: Screen, s: str, limit: int) -> int:
    """Draw at most limit cells of s. Returns how many cells were drawn."""
    if limit <= 0 or not s:
        return 0
    out = s[:limit]
    screen.draw(out)
    return len(out)


def draw_tab(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    # Hard budget for this tab (kitty computed this so all tabs can fit)
    start_x = before
    end_x = min(screen.columns, start_x + max(0, max_title_length))

    # If no space, do nothing
    if end_x <= start_x:
        return start_x

    # Base bar
    screen.cursor.bg = _rgb(BAR_BG)
    screen.cursor.fg = _rgb(EDGE_FG)

    # Left edge separator counts against our budget
    if start_x > 0:
        avail = end_x - screen.cursor.x
        _draw_limited(screen, SEP, avail)

    is_active = tab.is_active

    # Tab colors + underline for active
    if is_active:
        tab_bg, tab_fg = TAB_BG_ACTIVE, TAB_FG_ACTIVE
        screen.apply_sgr(f"58;2;{UL_R};{UL_G};{UL_B}")  # underline color
        screen.apply_sgr("4")                           # underline on
    else:
        tab_bg, tab_fg = TAB_BG_INACTIVE, TAB_FG_INACTIVE
        screen.apply_sgr("24")                          # underline off

    screen.cursor.bg = _rgb(tab_bg)
    screen.cursor.fg = _rgb(tab_fg)

    # Minimal content: " {index} "
    prefix = f"{PAD}{index}{PAD}"

    # Draw prefix within budget
    avail = end_x - screen.cursor.x
    used = _draw_limited(screen, prefix, avail)

    # If we ran out of space, close underline and return
    if screen.cursor.x >= end_x:
        if is_active:
            screen.apply_sgr("24")
        return end_x

    # Leave at least 1 cell for a trailing space/ellipsis
    # Compute remaining budget for title drawing
    avail = end_x - screen.cursor.x
    # If tiny space remains, draw ellipsis
    if avail <= 1:
        _draw_limited(screen, ELL, avail)
        if is_active:
            screen.apply_sgr("24")
        return end_x

    # Draw title constrained by remaining budget
    # draw_title will stop at the screen edge; we also cap the passed budget.
    title_budget = max(0, avail - 1)
    draw_title(draw_data, screen, tab, index, title_budget)

    # Fill the last cell as padding (keeps box feel)
    avail = end_x - screen.cursor.x
    _draw_limited(screen, PAD, avail)

    # Stop underline so it doesn't leak
    if is_active:
        screen.apply_sgr("24")

    # Restore bar colors for whatever comes next
    screen.cursor.bg = _rgb(BAR_BG)
    screen.cursor.fg = _rgb(EDGE_FG)

    return end_x

