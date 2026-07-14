"""The GATHER seam — turn a rendered component (html, css) into verdict-free FACTS. It DECIDES
nothing (the predicate library + conform() decide); it only observes. This is the profile-/host-
specific glue; everything above it is portable. Only STATICALLY-parseable facts are gathered here
(radius, anatomy, material presence, shadow presence, mechanic, focus recipe) — computed contrast
over a translucent surface + responsive-no-clip are renderer-dependent and are gathered by the
headless-probe (a declared later slice), never faked here. candidate_only.
"""
from __future__ import annotations

from collections import Counter
import re


def button_facts(html: str, css: str) -> dict:
    """Facts observable from `render_button`'s output. `css` may concatenate the rest + active +
    focus renders; the BASE rule is the first non-state `.cls { … }` block, the state recipes are
    the `.is-*` rules. Fail-closed (codex 1b-ii #1): if no base rule is parseable, material/shadow
    facts are `None` (not `False`) so a material/elevation predicate cannot pass on empty CSS."""
    base_m = re.search(r"\.[\w-]+\s*\{([^}]*)\}", css)   # first rule = the base `.cls { … }`
    base = base_m.group(1) if base_m else None

    m = re.search(r"border-radius:\s*(\d+)px", base) if base is not None else None
    radius_px = int(m.group(1)) if m else None

    # anatomy: Carbon emits a label node THEN a trailing icon sibling; the Apple capsules a
    # centered label (icon leading). Requires POSITIVE evidence of a rendered <button>, else None
    # (fail-closed) — an empty render must not pass an anatomy invariant.
    # label-left-icon-right requires a btn-label WITH text (codex: an empty-label Carbon DOM is not
    # positive evidence) BEFORE the btn-icon; centered-capsule requires a <button> with text.
    if (re.search(r'class="btn-label"[^>]*>[^<]*\w', html) and "btn-icon" in html
            and html.index("btn-label") < html.index("btn-icon")):
        anatomy = "label-left-icon-right"
    elif re.search(r"<button[^>]*>[^<]*\w", html):   # a <button> with actual text (empty <button></button> -> None)
        anatomy = "centered-capsule"
    else:
        anatomy = None

    # state mechanic: MUTUALLY EXCLUSIVE (codex 1b-ii #2). Count every press signal in `.is-active`;
    # resolve a mechanic ONLY when exactly one is present. Two signals (e.g. brightness + a token
    # swap) is ambiguous -> None -> the mechanic predicate fails, never a priority-picked pass.
    active = re.search(r"\.is-active\s*\{([^}]*)\}", css)
    active_css = active.group(1) if active else ""
    signals = []
    if "brightness(" in active_css:
        signals.append("glass-brightness")
    if re.search(r"\bopacity:", active_css):
        signals.append("opacity-dim")
    if "background-color" in active_css:
        signals.append("token-swap")
    mechanic = signals[0] if len(signals) == 1 else None

    # focus recipe: keyed on SPECIFIC ring geometry AND mutually exclusive (same discipline as the
    # chip). A rule with both a square inset and a halo is ambiguous -> None, never priority-picked.
    focus_recipe = _focus_recipe(css, (
        ("inset 0 0 0 2px", "square-2px-ring"),    # carbon: inset 1px+2px square ring
        ("0 0 0 5px", "capsule-halo"),             # liquid: 2px backdrop + 5px accent halo
        ("0 0 0 4px", "rounded-system-ring"),      # apple: single 4px rounded system ring
    ))

    return {
        "radius_px": radius_px,
        "anatomy": anatomy,
        "state_mechanic": mechanic,
        # None (not False) when no base rule; a `none` value is NOT presence (codex) -> fail closed
        "has_backdrop_filter": _has_prop(base, "backdrop-filter"),
        "has_box_shadow": _has_prop(base, "box-shadow"),
        "focus_recipe": focus_recipe,
    }


def _base_rule(css: str):
    """The base `.cls { … }` body (first non-state rule), or None if unparseable — shared by the
    component fact-gatherers so material/shadow facts fail closed (None) on empty CSS."""
    m = re.search(r"\.[\w-]+\s*\{([^}]*)\}", css)
    return m.group(1) if m else None


def _invisible_color(value: str) -> bool:
    """A colour that paints nothing: the `transparent`/`none` keywords OR a 0-alpha rgba/hsla."""
    v = value.strip()
    return (v in ("transparent", "none")
            or re.search(r"(?:rgba|hsla)\([^)]*,\s*0(?:\.0+)?\s*\)$", v) is not None)


def _has_prop(base, prop: str):
    """True iff `base` declares `prop` with a value that actually renders — NOT `none` (incl.
    `none !important`) and not empty. None if there is no base rule (fail-closed). codex:
    `backdrop-filter: none` / `box-shadow: none !important` must NOT read as present."""
    if base is None:
        return None
    for v in re.findall(rf"{prop}:\s*([^;]+)", base):
        v = v.replace("!important", "").strip()
        if v not in ("none", ""):
            return True
    return False


def _mechanic(css: str):
    """The MUTUALLY-EXCLUSIVE press mechanic read from `.is-active` (None if zero or >1 signals)."""
    active = re.search(r"\.is-active\s*\{([^}]*)\}", css)
    active_css = active.group(1) if active else ""
    signals = []
    if "brightness(" in active_css:
        signals.append("glass-brightness")
    if re.search(r"\bopacity:", active_css):
        signals.append("opacity-dim")
    if "background-color" in active_css:
        signals.append("token-swap")
    return signals[0] if len(signals) == 1 else None


def _focus_recipe(css: str, recipes: tuple[tuple[str, str], ...]):
    """The MUTUALLY-EXCLUSIVE focus recipe read from `.is-focus`.

    `recipes` is `(literal_signature, recipe_name)`. A missing focus rule OR multiple matching ring
    signatures returns None, so predicates fail closed instead of taking a priority branch.
    """
    focus = re.search(r"\.is-focus\s*\{([^}]*)\}", css)
    focus_css = focus.group(1) if focus else ""
    signals = [name for needle, name in recipes if needle in focus_css]
    return signals[0] if len(signals) == 1 else None


def chip_facts(html: str, css: str) -> dict:
    """Verdict-free facts for the chip/tag (instance #2). Same fail-closed / mutually-exclusive
    discipline as `button_facts`; chip-specific: `label-dismiss` anatomy (a trailing `×` close
    button), an `outline: 2px` focus recipe (Carbon Tag, distinct from the button's inset ring),
    and `typography_case` (sentence unless a `text-transform: uppercase` is emitted)."""
    base = _base_rule(css)
    m = re.search(r"border-radius:\s*(\d+)px", base) if base is not None else None
    radius_px = int(m.group(1)) if m else None

    # label-dismiss: a label node FOLLOWED BY a trailing dismiss <button> (codex chip #3 — a bare
    # `chip-dismiss` substring anywhere is not enough; it must be the close BUTTON after the label).
    # Requires POSITIVE evidence of a rendered chip pill, else None (fail-closed on an empty render).
    dismiss = '<button class="chip-dismiss"'
    # label-dismiss requires a chip-label WITH text (codex: empty label span is not evidence)
    if (re.search(r'class="chip-label"[^>]*>[^<]*\w', html) and dismiss in html
            and html.index("chip-label") < html.index(dismiss)):
        anatomy = "label-dismiss"
    elif re.search(r'<span class="chip-[^"]*"[^>]*>[^<]*\w', html):   # a chip pill with actual text (empty span -> None)
        anatomy = "centered-label"
    else:
        anatomy = None

    # focus recipe: MUTUALLY EXCLUSIVE — count signals, None on zero or >1 (same discipline as the
    # mechanic; codex chip N1 — `outline: 2px` + a halo can't both resolve to outline-2px).
    focus_recipe = _focus_recipe(css, (
        ("outline: 2px", "outline-2px"),            # carbon Tag: 2px solid outline + 1px offset
        ("0 0 0 5px", "capsule-halo"),             # liquid: capsule halo
        ("0 0 0 4px", "rounded-system-ring"),      # apple: rounded system ring
    ))

    return {
        "radius_px": radius_px,
        "anatomy": anatomy,
        "state_mechanic": _mechanic(css),
        "has_backdrop_filter": _has_prop(base, "backdrop-filter"),
        "has_box_shadow": _has_prop(base, "box-shadow"),
        "focus_recipe": focus_recipe,
        # fail-closed (codex chip #2): None (not "sentence") when no base rule -> chip_sentence_case fails
        "typography_case": (None if base is None
                            else ("upper" if "text-transform: uppercase" in base else "sentence")),
    }


# Token-only is decided within a CLOSED shell structure (codex A1c). Rather than defensively out-parse
# arbitrary CSS (specificity, @media, comments, obscure colour props), the gatherer requires the host
# chrome to be a CLOSED, SIMPLE structure — one root rule `.ps-<lang>` + descendant `.ps-<lang> .child`
# rules, no @-rules / attribute / pseudo selectors / combinators — so specificity conflicts, @media
# nesting, and attribute-selector overrides are UNCONSTRUCTABLE. Then every declaration VALUE must be
# composed ONLY of var(--…) refs + structural keywords + a 1px hairline: any colour of any form
# (hex / rgb() / hsl() / color-mix() / named / currentColor) in ANY property is caught, no hand list.
_VAR_REF = re.compile(r"var\(--[\w-]+\)")
_PX = re.compile(r"-?\d*\.?\d+px", re.I)
_DIM = re.compile(r"-?\d*\.?\d+[a-z%]*", re.I)
# NB: `inherit`/`initial`/`unset` are deliberately NOT here (codex A1d) — `color: initial` would paint the
# browser default, escaping the token system; a token-only shell states every value explicitly. System
# colours (CanvasText / ButtonText / AccentColor …) are likewise not here, so they redden.
_SAFE_VALUE_WORDS = frozenset("""
 solid dashed dotted double groove ridge inset outset none hidden transparent auto
 normal bold bolder lighter italic oblique underline overline line-through uppercase lowercase capitalize
 center left right start end justify flex block inline grid wrap nowrap visible collapse pointer default
 middle top bottom baseline stretch content-box border-box relative absolute fixed sticky static
""".split())


def _strip_noise(css: str) -> str:
    """The host-chrome CSS with comments + the declared `:root { … }` token blocks removed (so a colour
    hidden after a `/* … */` comment or inside `:root` cannot slip past the value scan)."""
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    return re.sub(r':root(?:\[data-theme="[\w-]+"\])?\s*\{[^}]*\}', " ", css)


def _css_rules(css: str):
    """(selector, [(prop, value), …]) per rule."""
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        decls = [(p.strip().lower(), v.strip())
                 for d in m.group(2).split(";") if ":" in d
                 for p, _, v in [d.partition(":")]]
        yield m.group(1).strip(), decls


def _value_offtokens(value: str) -> int:
    """Off-token literals in ONE declaration VALUE (prop-INDEPENDENT). Drop var(--…) refs + dimensions,
    then every leftover WHOLE word must be a structural keyword — so a named colour / currentColor in ANY
    property (incl. obscure ones: stop-color, -webkit-text-fill-color, …) is caught with no property list.
    Also flags any hex, any non-var function `(`, and any px other than the 1px hairline."""
    resid = _VAR_REF.sub(" ", value)
    bad = 0
    if "#" in resid:
        bad += 1
    if "(" in resid:                                         # any NON-var function: rgb()/color-mix()/calc()…
        bad += 1
    bad += sum(1 for px in _PX.findall(resid) if px.lower() != "1px")
    resid = _DIM.sub(" ", resid)                             # drop numbers/dimensions; only keywords remain
    bad += sum(1 for w in re.findall(r"(?<![\w.])[A-Za-z][\w-]*", resid)
               if w.lower() not in _SAFE_VALUE_WORDS)
    return bad


def content_offtokens(css: str, allowed_px: frozenset = frozenset(),
                      allowed_words: frozenset = frozenset()) -> list[str]:
    """Verdict-free scan of page CONTENT CSS — the styles a page ships INSIDE a governed shell
    (verdict tables, legends, stages; codex A3 #1). Content may lay itself out, but a COLOUR
    decision of any form (hex / colour function / named / system / initial-inherit-unset escape)
    or a px outside the page's EXPLICIT structural allowlist is off-token — colour and scale
    belong to the shell's tokens. Returns the offending literals (empty == token-only content),
    so a page's declared allowlist is the ONLY escape and it can never admit a colour.

    Unlike the chrome scan, `:root` is NOT stripped here (codex A3b #1): token DECLARATION belongs
    to the shell's provenance-pinned `root_block` — content may only REFERENCE vars, so a `:root`
    block (which would override shell tokens, loading after them) or ANY custom-property
    declaration in content is itself flagged, colour or not."""
    bad: list[str] = []
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)     # comments only — :root stays visible
    if "@" in css:                                       # codex A3c: an at-rule PRELUDE is never seen by
        bad.append("@-rule: content CSS is @-rule-free"  # the body scan (`@media (min-width: 8px)` /
                   " (a prelude could smuggle literals)")  # `@supports (background: #f00)`) — closed out
    for sel, decls in _css_rules(css):
        if ":root" in sel.lower():
            bad.append(f"{sel}: content may not declare a :root block")
        for prop, val in decls:
            if prop.startswith("--"):
                bad.append(f"{prop}: content may not mint/override a token")
                continue
            resid = _VAR_REF.sub(" ", val)
            bad += re.findall(r"#[0-9a-fA-F]{3,8}\b", resid)
            if "(" in resid:                                 # any NON-var function: rgb()/color-mix()/calc()…
                bad.append(f"{prop}: non-var function")
            bad += [px for px in _PX.findall(resid)
                    if px.lower() != "1px" and px.lower() not in allowed_px]
            resid = _DIM.sub(" ", resid)
            bad += [w for w in re.findall(r"(?<![\w.])[A-Za-z][\w-]*", resid)
                    if w.lower() not in _SAFE_VALUE_WORDS and w.lower() not in allowed_words]
    return bad


_CSS_NUMBER = re.compile(
    r"(?<![A-Za-z0-9_.-])-?(?:\d+\.\d+|\d+)(?:[A-Za-z]+|%)?"
)


def css_numeric_occurrences(css: str) -> list[dict]:
    """Return an exact multiset of numeric CSS literals with structural context.

    The governed dashboard emitter uses a deliberately closed grammar: ordinary rules and nested
    at-rules, with no braces inside declaration values. This parser is small by design and rejects
    malformed/unbalanced input instead of guessing. It is a fact producer; policy lives in DATA.
    """
    source = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    observed: Counter[tuple[str, str, str, str]] = Counter()

    def normalized(value: str) -> str:
        return " ".join(value.split())

    def tokens(value: str) -> list[str]:
        return [match.group(0) for match in _CSS_NUMBER.finditer(value)]

    def walk(fragment: str, contexts: tuple[str, ...]) -> None:
        cursor = 0
        while cursor < len(fragment):
            opening = fragment.find("{", cursor)
            if opening < 0:
                if fragment[cursor:].strip():
                    raise ValueError("CSS text outside a governed rule")
                return
            header = normalized(fragment[cursor:opening])
            if not header:
                raise ValueError("CSS rule has an empty header")
            depth = 1
            closing = opening + 1
            while closing < len(fragment) and depth:
                if fragment[closing] == "{":
                    depth += 1
                elif fragment[closing] == "}":
                    depth -= 1
                closing += 1
            if depth:
                raise ValueError("CSS rule has unbalanced braces")
            body = fragment[opening + 1:closing - 1]
            context = " > ".join(contexts)
            if header.startswith("@"):
                for token in tokens(header):
                    observed[(context, "", "@prelude", token)] += 1
                walk(body, contexts + (header,))
            else:
                if "{" in body or "}" in body:
                    raise ValueError("nested ordinary CSS rule")
                for declaration in body.split(";"):
                    if not declaration.strip():
                        continue
                    prop, separator, value = declaration.partition(":")
                    if not separator or not prop.strip() or not value.strip():
                        raise ValueError(f"malformed CSS declaration in {header!r}")
                    for token in tokens(value):
                        observed[(context, header, prop.strip().lower(), token)] += 1
            cursor = closing

    walk(source, ())
    return [
        {
            "context": context,
            "selector": selector,
            "property": prop,
            "value": value,
            "count": count,
        }
        for (context, selector, prop, value), count in sorted(observed.items())
    ]


def pageshell_facts(html: str, css: str) -> dict:
    """Verdict-free facts for the page CHROME (`render_page_shell`). The host chrome must be CLOSED (one
    `.ps-<lang>` root rule + descendant `.ps-<lang> .child`/element rules only; no @-rules / attribute /
    pseudo selectors) AND token-only per value. With a closed structure the single root rule's background
    is unambiguous (no specificity/@media games). Fail-closed: presence facts default False. The `:root`
    VALUE provenance (== resolve_tokens) is pinned by test_page_shell, not decided here."""
    shell_m = re.search(r'<div class="(ps-[\w-]+)"', html)
    shell_cls = shell_m.group(1) if shell_m else None
    body = _strip_noise(css)
    has_atrule = "@" in body
    rules = list(_css_rules(body))
    offtoken = sum(_value_offtokens(v) for _, decls in rules for _, v in decls)

    root_sel = f".{shell_cls}" if shell_cls else None
    # closed: every selector is the root or a descendant `.ps-<lang> <simple>` chain (class or element),
    # no commas / attribute / pseudo / child-sibling combinators, and no @-rule anywhere.
    allowed = re.compile(rf"^\.{re.escape(shell_cls)}(?:\s+\.?[\w-]+)*$") if shell_cls else None
    selectors = [sel.strip() for sel, _ in rules]
    root_rule_count = sum(1 for s in selectors if s == root_sel)
    shell_closed = bool(shell_cls) and not has_atrule and bool(selectors) \
        and all(allowed.match(s) for s in selectors)

    root_bg = [v for sel, decls in rules if sel.strip() == root_sel
               for p, v in decls if p in ("background", "background-color")]
    uses_backdrop_var = (bool(root_bg) and _value_offtokens(root_bg[-1]) == 0
                         and _VAR_REF.findall(root_bg[-1]) == ["var(--backdrop)"])

    has_title = bool(re.search(r'class="ps-title"[^>]*>[^<]*\w', html))
    crumbs_m = re.search(r'class="ps-crumbs"[^>]*>(.*?)</p>', html, re.S)
    has_breadcrumb_link = bool(crumbs_m and re.search(r'<a[^>]+href="[^"]+"[^>]*>[^<]*\w', crumbs_m.group(1)))

    # LAYOUT facts (design-audit D-SHELL) — fail-closed: absent column/ramp vars -> False/None.
    main_m = (re.search(rf"\.{re.escape(shell_cls)}\s+\.ps-main\s*\{{([^}}]*)\}}", css)
              if shell_cls else None)
    has_content_column = bool(
        main_m and "max-width: var(--ps-measure-page)" in main_m.group(1)
        and re.search(r"margin:\s*0 auto", main_m.group(1))
        and re.search(r'<div class="ps-main"[^>]*>', html))

    def _root_px(var: str):
        m = re.search(rf"{re.escape(var)}:\s*(-?\d+(?:\.\d+)?)px", css)
        return float(m.group(1)) if m else None

    t_title, t_h2, t_body = (_root_px("--ps-type-title"), _root_px("--ps-type-h2"),
                             _root_px("--ps-type-body"))
    type_ramp_tiered = (None not in (t_title, t_h2, t_body)) and t_title > t_h2 > t_body

    # D-SHELL-2 grouping facts (gate MF-A, precise definition): a CHROMED class = the rightmost
    # class of a shell rule declaring a painting background AND (a border or border-radius).
    # Depth over a balanced tag stack; an unbalanced parse -> None (fail-closed). The count fact
    # kills vacuity: "flat" is only claimable when >=1 chromed box actually rendered.
    chromed: set = set()
    for sel, decls in rules:
        props = dict(decls)
        bg = props.get("background") or props.get("background-color") or ""
        painted = bg.strip() not in ("", "transparent", "none", "0")
        if painted and ("border" in props or "border-radius" in props):
            classes = re.findall(r"\.([\w-]+)", sel)
            if classes:
                chromed.add(classes[-1])

    def _nesting(text: str):
        depth_max, count, stack = 0, 0, []
        for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*)>", text):
            close, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
            if tag in ("input", "br", "img", "hr", "meta", "link") or attrs.rstrip().endswith("/"):
                continue
            if close:
                if not stack or stack[-1][0] != tag:
                    return None, None
                stack.pop()
            else:
                cm = re.search(r'class="([^"]*)"', attrs)
                is_chr = bool(cm and chromed & set(cm.group(1).split()))
                if is_chr:
                    count += 1
                    depth_max = max(depth_max, 1 + sum(1 for _, c in stack if c))
                stack.append((tag, is_chr))
        return (None, None) if stack else (depth_max, count)

    chrome_nesting_depth, chromed_box_count = _nesting(html)
    return {
        "body_offtoken_count": offtoken,
        "shell_closed": shell_closed,
        "root_rule_count": root_rule_count,
        "uses_backdrop_var": uses_backdrop_var,
        "has_title": has_title,
        "has_breadcrumb_link": has_breadcrumb_link,
        "has_content_column": has_content_column,
        "type_ramp_tiered": type_ramp_tiered,
        "pad_px": _root_px("--ps-pad"),
        "chrome_nesting_depth": chrome_nesting_depth,
        "chromed_box_count": chromed_box_count,
    }


def card_facts(html: str, css: str) -> dict:
    """Verdict-free STRUCTURAL facts for the card / grouped metric surface (instance #3). Only the
    composition is gathered here — declared box structure, NOT rendered ink (the 'content fills the
    card' verdict is a JUDGMENT concern, gathered by a visual receipt, never faked from a static
    parse). Fail-closed: a missing container/row rule -> the pattern facts are False/None so the
    predicate fails."""
    container = _base_rule(css)              # first rule = the `.card-<cls>` container
    m = re.search(r"border-radius:\s*(\d+)px", container) if container is not None else None
    radius_px = int(m.group(1)) if m else None

    container_count = html.count("card-group")     # each container carries the `card-group` marker
    row_count = len(re.findall(r'class="card-row"(?=[\s>])', html))

    row_m = re.search(r"\.card-row\s*\{([^}]*)\}", css)   # the row base rule (not the `+` divider)
    row_body = row_m.group(1) if row_m else None
    # rows carry NO independent background (incl. -color/-image longhands, codex card #2) and NO
    # radius (incl. any `*-radius` longhand). A row with its own chrome IS the grid-of-tiles AI look.
    row_has_own_bg = bool(row_body is not None and any(
        v.strip() not in ("transparent", "none")
        for v in re.findall(r"background(?:-color|-image)?:\s*([^;]+)", row_body)))
    rows_chromeless = bool(
        row_body is not None
        and "-radius" not in row_body
        and not row_has_own_bg)
    # horizontal AXIS: flex, and no `column` in flex-direction OR the flex-flow shorthand (codex card #3)
    rows_horizontal = bool(
        row_body is not None
        and "display: flex" in row_body
        and not re.search(r"flex-(?:direction|flow):[^;]*column", row_body))

    # a VISIBLE 1px divider — `border-top: 1px solid <color>` with a colour that actually paints
    # (codex: `1px solid transparent` AND `1px solid rgba(0,0,0,0)` are invisible, not a hairline).
    div_m = re.search(r"\.card-row\s*\+\s*\.card-row\s*\{([^}]*)\}", css)
    div_color = re.search(r"border-top:\s*1px\s+solid\s+([^;]+)", div_m.group(1)) if div_m else None
    divider_1px = bool(div_color and not _invisible_color(div_color.group(1)))

    return {
        "radius_px": radius_px,
        "container_count": container_count,
        "row_count": row_count,
        "rows_chromeless": rows_chromeless,
        "rows_horizontal": rows_horizontal,
        "divider_1px": divider_1px,
        "has_backdrop_filter": _has_prop(container, "backdrop-filter"),
        "has_box_shadow": _has_prop(container, "box-shadow"),
    }


def switcher_facts(html: str, css: str) -> dict:
    """Verdict-free facts for the switchable segmented theme control."""
    from scripts.rendering.design import loader

    html_profiles = tuple(re.findall(r'data-theme-set="([a-z0-9-]+)"', html))
    css_profiles = tuple(dict.fromkeys(re.findall(
        r':root\[data-theme="([a-z0-9-]+)"\] \.theme-switcher\s*\{', css)))
    profiles = {}
    expected_profiles = {}

    def declaration_map(body: str) -> dict[str, str]:
        return {
            prop.strip(): value.strip()
            for declaration in body.split(";") if declaration.strip()
            for prop, separator, value in [declaration.partition(":")]
            if separator and prop.strip() and value.strip()
        }

    for profile in css_profiles:
        root = re.search(
            rf':root\[data-theme="{re.escape(profile)}"\] \.theme-switcher\s*\{{([^}}]*)\}}',
            css,
        )
        option = re.search(
            rf':root\[data-theme="{re.escape(profile)}"\] \.theme-switcher '
            rf'\.theme-option\s*\{{([^}}]*)\}}',
            css,
        )
        root_body = root.group(1) if root else ""
        option_body = option.group(1) if option else ""
        height = re.search(r"min-height:\s*(\d+)px", option_body)
        radius = re.search(r"border-radius:\s*(\d+)px", option_body)
        justify = re.search(r"justify-content:\s*([\w-]+)", option_body)
        def state_body(suffix: str) -> str:
            match = re.search(
                rf':root\[data-theme="{re.escape(profile)}"\] \.theme-switcher '
                rf'\.theme-option{suffix}\s*\{{([^}}]*)\}}',
                css,
            )
            return match.group(1).strip() if match else ""

        icon_rule = re.search(
            rf':root\[data-theme="{re.escape(profile)}"\] \.theme-switcher '
            rf'\.theme-option-icon\s*\{{([^}}]*)\}}',
            css,
        )
        icon_body = icon_rule.group(1) if icon_rule else ""
        hover_body = state_body(":hover")
        active_body = state_body(":active")
        focus_body = state_body(":focus-visible")
        selected_body = state_body(r'\[aria-pressed="true"\]')
        disabled_body = state_body(":disabled")
        if "var(--button-active-background)" in active_body:
            mechanic = "token-swap"
        elif "filter: brightness(" in active_body:
            mechanic = "glass-brightness"
        elif re.search(r"\bopacity:\s*0\.4\b", active_body):
            mechanic = "opacity-dim"
        else:
            mechanic = None
        if "outline: 3px" in focus_body and "60%" in focus_body:
            focus_recipe = "capsule-halo"
        elif "outline: 2px" in focus_body and "outline-offset: -2px" in focus_body:
            focus_recipe = "square-2px-ring"
        elif "outline: 4px" in focus_body and "50%" in focus_body:
            focus_recipe = "rounded-system-ring"
        else:
            focus_recipe = None
        anatomy = ("label-left-icon-right"
                   if justify and justify.group(1) == "space-between" and "display: block" in icon_body
                   else ("centered-capsule"
                         if justify and justify.group(1) == "center" and "display: none" in icon_body
                         else None))
        profiles[profile] = {
            "height_px": int(height.group(1)) if height else None,
            "radius_px": int(radius.group(1)) if radius else None,
            "anatomy": anatomy,
            "state_mechanic": mechanic,
            "focus_recipe": focus_recipe,
            "hover_nonempty": bool(hover_body),
            "active_nonempty": bool(active_body),
            "focus_nonempty": bool(focus_body),
            "state_css": {
                "hover": declaration_map(hover_body),
                "active": declaration_map(active_body),
                "focus-visible": declaration_map(focus_body),
                "selected": declaration_map(selected_body),
                "disabled": declaration_map(disabled_body),
            },
        }
        button = loader.load(profile)["components"]["button"]
        expected_profiles[profile] = {
            "height_px": button["height_px"],
            "radius_px": button["radius_px"],
            "anatomy": button["anatomy"],
            "state_mechanic": button["state_mechanic"],
            "focus_recipe": button["focus_recipe"],
            "hover_nonempty": True,
            "active_nonempty": True,
            "focus_nonempty": True,
            "state_css": button["switcher_css"],
        }
    return {
        "html_profiles": html_profiles,
        "css_profiles": css_profiles,
        "button_count": html.count('class="theme-option"'),
        "pressed_count": len(re.findall(r'class="theme-option"[^>]*aria-pressed="true"', html)),
        "profiles": profiles,
        "expected_profiles": expected_profiles,
        "has_rest": re.search(r"\.theme-option\s*\{", css) is not None,
        "icon_count": html.count('class="theme-option-icon"'),
        "has_pressed": '.theme-option[aria-pressed="true"]' in css,
        "has_disabled": ".theme-option:disabled" in css,
    }
