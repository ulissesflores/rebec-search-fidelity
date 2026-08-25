#!/usr/bin/env python3
"""Draw Figure 1: the five measured links of defect 1, as vector SVG.

Every label is a fact carried by ``output/public-search-vs-database.json``, by the
served ``cse.js``, or by the certificate read at measurement time. The figure
asserts nothing the report does not.

Written with the standard library alone -- no plotting stack, no font
rasterisation -- which is what makes the output byte-identical on any machine.
That determinism is why the figures are folded into ``artifact_root`` and is
asserted by ``tests/test_determinism.py``.

Usage
-----
``python3 code/make_figure.py [--lang en|pt]``  ->  ``output/figures/fig1-defect1-chain[-pt].svg``
"""

from __future__ import annotations

import argparse
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent

EN = {
    "title": "Figure 1. Defect 1: the five measured links between the registry's own"
    " search box and a browser security interstitial.",
    "steps": [
        (
            "1. The visitor uses the search box",
            "ReBEC home page, https://ensaiosclinicos.gov.br - typed: dengue",
        ),
        (
            "2. The search widget decides where to go",
            "cse.js?cx=ad5f3224a2a0fa826 carries one URL for this site:",
            "http://www.ensaiosclinicos.gov.br/search/query/simple",
        ),
        (
            "3. The navigation is promoted from http to https",
            "mechanism NOT isolated - either the site's own header",
            "Content-Security-Policy: upgrade-insecure-requests, or the browser's HTTPS upgrade",
        ),
        (
            "4. The https request meets a certificate that does not cover the host",
            "www.ensaiosclinicos.gov.br and ensaiosclinicos.gov.br both resolve to 140.82.26.58,",
            "but the certificate carries a single SAN: DNS:ensaiosclinicos.gov.br",
        ),
        (
            "5. The browser stops. The search never runs.",
            "Chrome shows a privacy error; no request ever reaches the registry",
        ),
    ],
    "foot": "All links measured 25 August 2026. Reproduce: see section 6.",
}
PT = {
    "title": "Figura 1. Defeito 1: os cinco elos medidos entre a caixa de busca do próprio"
    " registro e o aviso de segurança do navegador.",
    "steps": [
        (
            "1. O visitante usa a caixa de busca",
            "página inicial do ReBEC, https://ensaiosclinicos.gov.br - digitado: dengue",
        ),
        (
            "2. O buscador decide para onde ir",
            "o cse.js?cx=ad5f3224a2a0fa826 traz uma única URL deste site:",
            "http://www.ensaiosclinicos.gov.br/search/query/simple",
        ),
        (
            "3. A navegação é promovida de http para https",
            "mecanismo NÃO isolado - ou o cabeçalho do próprio site",
            "Content-Security-Policy: upgrade-insecure-requests, ou a promoção do navegador",
        ),
        (
            "4. A requisição https bate num certificado que não cobre o host",
            "www.ensaiosclinicos.gov.br e ensaiosclinicos.gov.br resolvem para 140.82.26.58,",
            "mas o certificado traz uma SAN única: DNS:ensaiosclinicos.gov.br",
        ),
        (
            "5. O navegador para. A busca nunca acontece.",
            "o Chrome exibe um erro de privacidade; nenhuma requisição chega ao registro",
        ),
    ],
    "foot": "Todos os elos medidos em 25 de agosto de 2026. Reprodução: ver seção 6.",
}

WIDTH, BOX_WIDTH, BOX_X, GAP = 660, 600, 30, 22
SANS = "Helvetica, Arial, 'Liberation Sans', sans-serif"
MONO = "'DejaVu Sans Mono', Menlo, Consolas, monospace"
MONO_MARKERS = ("http", "cse.js", "DNS:", "140.82")


def build(spec: dict) -> str:
    """Render one language's figure to an SVG document.

    Parameters
    ----------
    spec : dict
        ``title``, ``steps`` (each a tuple of heading plus detail lines) and ``foot``.

    Returns
    -------
    str
        A complete, self-contained SVG document.
    """
    parts: list[str] = []
    cut = spec["title"].rfind(" ", 0, 75)  # wrap on a word, never mid-word
    for k, line in enumerate((spec["title"][:cut], spec["title"][cut + 1 :])):
        parts.append(
            f'<text x="{BOX_X}" y="{34 + 20 * k}" font-family="{SANS}" font-size="15" '
            f'font-weight="bold" fill="#111">{escape(line)}</text>'
        )

    y = 74
    for i, step in enumerate(spec["steps"]):
        height = 34 + 18 * (len(step) - 1)
        last = i == len(spec["steps"]) - 1
        stroke, fill = ("#8a1f1f", "#fdf3f3") if last else ("#333", "#fbfbfb")
        parts.append(
            f'<rect x="{BOX_X}" y="{y}" width="{BOX_WIDTH}" height="{height}" rx="5" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
        )
        parts.append(
            f'<text x="{BOX_X + 14}" y="{y + 21}" font-family="{SANS}" font-size="13.5" '
            f'font-weight="bold" fill="#111">{escape(step[0])}</text>'
        )
        for j, line in enumerate(step[1:]):
            family = MONO if any(m in line for m in MONO_MARKERS) else SANS
            parts.append(
                f'<text x="{BOX_X + 14}" y="{y + 38 + 18 * j}" font-family="{family}" '
                f'font-size="11.5" fill="#333">{escape(line)}</text>'
            )
        if not last:
            mid = BOX_X + BOX_WIDTH / 2
            parts.append(
                f'<line x1="{mid}" y1="{y + height}" x2="{mid}" y2="{y + height + GAP}" '
                f'stroke="#333" stroke-width="1.4" marker-end="url(#arrow)"/>'
            )
        y += height + GAP

    y += 8
    parts.append(
        f'<text x="{BOX_X}" y="{y}" font-family="{SANS}" font-size="11" '
        f'fill="#555">{escape(spec["foot"])}</text>'
    )
    body = "\n  ".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{y + 22}" '
        f'viewBox="0 0 {WIDTH} {y + 22}" role="img">\n'
        f'  <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#333"/></marker>'
        f"</defs>\n"
        f'  <rect width="100%" height="100%" fill="#ffffff"/>\n  {body}\n</svg>\n'
    )


def main() -> None:
    """Write the figure for the requested language."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lang", choices=["en", "pt"], default="en")
    args = ap.parse_args()
    name = "fig1-defect1-chain.svg" if args.lang == "en" else "fig1-defect1-chain-pt.svg"
    dest = ROOT / "output" / "figures" / name
    dest.write_text(build(EN if args.lang == "en" else PT), encoding="utf-8")
    print(f"{dest}  ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
