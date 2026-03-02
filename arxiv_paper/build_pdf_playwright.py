#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright


PRINT_CSS = r"""
@page { size: Letter; margin: 1in; }

html { font-size: 11pt; }
body {
  font-family: "Times New Roman", Times, serif;
  line-height: 1.35;
  color: #111;
  counter-reset: fig tbl lst;
}

h1, h2, h3 { page-break-after: avoid; }
figure, table { page-break-inside: avoid; }

/* Make pandoc's title block look closer to a paper header */
h1.title { font-size: 18pt; margin-bottom: 0.1in; text-align: center; }
p.author, p.date { text-align: center; margin-top: 0; margin-bottom: 0.06in; }

/* Reduce excessive spacing in standalone HTML */
p { margin: 0.08in 0; }
ul, ol { margin: 0.08in 0 0.08in 0.25in; }

/* Figures injected by this script */
figure { counter-increment: fig; }
.figure-diagram { margin: 0.12in auto 0.08in auto; max-width: 6.5in; }
.figure-diagram svg { width: 100%; height: auto; display: block; }
figcaption { font-size: 10pt; color: #333; margin-top: 6px; }
figure > figcaption::before {
  content: "Figure " counter(fig) ". ";
  font-weight: 600;
}

/* Tables */
table { counter-increment: tbl; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 6px 8px; vertical-align: top; }
th { background: #f5f5f5; }
table > caption::before {
  content: "Table " counter(tbl) ". ";
  font-weight: 600;
}

/* Code / listings */
pre[data-caption] { counter-increment: lst; }
pre {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  padding: 10px 12px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 9.5pt;
}
pre code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
pre[data-caption]::before {
  content: "Listing " counter(lst) ". " attr(data-caption);
  display: block;
  margin-bottom: 6px;
  font-style: italic;
  color: #343a40;
}

/* Links */
a { color: #0645ad; text-decoration: none; }
a:hover { text-decoration: underline; }
"""


def _svg_wrap(svg: str) -> str:
    return f'<div class="figure-diagram">{svg}</div>'


SVG_BY_FIGURE_ID: dict[str, str] = {
    "fig:aasu": _svg_wrap(
        r"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 410" role="img" aria-label="AASU components diagram">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">
      <path d="M0,0 L12,4 L0,8 Z" fill="#343a40" />
    </marker>
  </defs>
  <style>
    .box { fill: #f8f9fa; stroke: #343a40; stroke-width: 1.4; }
    .hdr { fill: #e7f5ff; stroke: #1c7ed6; stroke-width: 1.6; }
    .t1 { font: 600 18px "Times New Roman", Times, serif; fill: #111; }
    .t2 { font: 14px "Times New Roman", Times, serif; fill: #111; }
    .arrow { stroke: #343a40; stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
  </style>

  <rect x="140" y="18" width="440" height="56" rx="10" ry="10" class="hdr"/>
  <text x="360" y="44" text-anchor="middle" class="t1">AASU</text>
  <text x="360" y="64" text-anchor="middle" class="t2">(versioned configuration snapshot)</text>

  <rect x="140" y="98" width="440" height="36" rx="8" ry="8" class="box"/>
  <rect x="140" y="142" width="440" height="36" rx="8" ry="8" class="box"/>
  <rect x="140" y="186" width="440" height="36" rx="8" ry="8" class="box"/>
  <rect x="140" y="230" width="440" height="36" rx="8" ry="8" class="box"/>
  <rect x="140" y="274" width="440" height="36" rx="8" ry="8" class="box"/>
  <rect x="140" y="318" width="440" height="36" rx="8" ry="8" class="box"/>
  <rect x="140" y="362" width="440" height="36" rx="8" ry="8" class="box"/>

  <text x="160" y="122" class="t2">P — Prompt package</text>
  <text x="160" y="166" class="t2">M — Model instance &amp; parameters</text>
  <text x="160" y="210" class="t2">R — Retrieval (RAG) configuration</text>
  <text x="160" y="254" class="t2">T — Tools / MCP configuration</text>
  <text x="160" y="298" class="t2">K — Runtime constraints / guardrails</text>
  <text x="160" y="342" class="t2">H — History / memory configuration</text>
  <text x="160" y="386" class="t2">S — Skill configuration</text>

  <path d="M360,74 L360,90" class="arrow"/>
  <path d="M360,134 L360,138" class="arrow"/>
  <path d="M360,178 L360,182" class="arrow"/>
  <path d="M360,222 L360,226" class="arrow"/>
  <path d="M360,266 L360,270" class="arrow"/>
  <path d="M360,310 L360,314" class="arrow"/>
  <path d="M360,354 L360,358" class="arrow"/>
</svg>
""".strip()
    ),
    "fig:runtime": _svg_wrap(
        r"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 520" role="img" aria-label="AASU runtime flow diagram">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">
      <path d="M0,0 L12,4 L0,8 Z" fill="#343a40" />
    </marker>
  </defs>
  <style>
    .box { fill: #f8f9fa; stroke: #343a40; stroke-width: 1.4; }
    .kbox { fill: #fff9db; stroke: #f08c00; stroke-width: 1.4; }
    .decision { fill: #fff4e6; stroke: #e8590c; stroke-width: 1.4; }
    .t { font: 14px "Times New Roman", Times, serif; fill: #111; }
    .tB { font: 600 14px "Times New Roman", Times, serif; fill: #111; }
    .arrow { stroke: #343a40; stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
  </style>

  <rect x="330" y="20" width="240" height="44" rx="10" ry="10" class="box"/>
  <text x="450" y="47" text-anchor="middle" class="tB">User input</text>

  <rect x="300" y="86" width="300" height="52" rx="10" ry="10" class="kbox"/>
  <text x="450" y="112" text-anchor="middle" class="tB">K: pre-guardrails</text>
  <text x="450" y="130" text-anchor="middle" class="t">(policy checks, limits)</text>

  <polygon points="450,160 530,208 450,256 370,208" class="decision"/>
  <text x="450" y="204" text-anchor="middle" class="tB">R enabled?</text>

  <rect x="70" y="282" width="290" height="58" rx="10" ry="10" class="box"/>
  <text x="215" y="308" text-anchor="middle" class="tB">R: retrieval</text>
  <text x="215" y="326" text-anchor="middle" class="t">(top-k context)</text>

  <rect x="320" y="282" width="260" height="70" rx="10" ry="10" class="box"/>
  <text x="450" y="308" text-anchor="middle" class="tB">P: prompt assembly</text>
  <text x="450" y="326" text-anchor="middle" class="t">(system + dev + user + ctx)</text>

  <rect x="320" y="374" width="260" height="58" rx="10" ry="10" class="box"/>
  <text x="450" y="400" text-anchor="middle" class="tB">M: model call</text>
  <text x="450" y="418" text-anchor="middle" class="t">(params / decoding)</text>

  <polygon points="450,448 530,486 450,524 370,486" class="decision" transform="translate(0,-40)"/>
  <text x="450" y="450" text-anchor="middle" class="tB">Tool call?</text>

  <rect x="600" y="282" width="260" height="70" rx="10" ry="10" class="box"/>
  <text x="730" y="308" text-anchor="middle" class="tB">T: tool runtime</text>
  <text x="730" y="326" text-anchor="middle" class="t">(permissions + sandbox)</text>

  <rect x="600" y="374" width="260" height="58" rx="10" ry="10" class="kbox"/>
  <text x="730" y="400" text-anchor="middle" class="tB">K: post-guardrails</text>
  <text x="730" y="418" text-anchor="middle" class="t">(safe output handling)</text>

  <rect x="600" y="454" width="260" height="44" rx="10" ry="10" class="box"/>
  <text x="730" y="481" text-anchor="middle" class="tB">Response</text>

  <!-- main flow arrows -->
  <path d="M450,64 L450,86" class="arrow"/>
  <path d="M450,138 L450,160" class="arrow"/>

  <path d="M370,208 L260,208 L260,282" class="arrow"/>
  <text x="292" y="196" class="t">yes</text>

  <path d="M530,208 L660,208 L660,282" class="arrow"/>
  <text x="602" y="196" class="t">no</text>

  <path d="M360,311 L320,311" class="arrow"/>
  <path d="M450,352 L450,374" class="arrow"/>
  <path d="M450,432 L450,448" class="arrow"/>

  <!-- tool branch -->
  <path d="M530,446 L730,446 L730,352" class="arrow"/>
  <text x="618" y="434" class="t">yes</text>

  <path d="M450,446 L650,446 L650,374" class="arrow"/>
  <text x="536" y="434" class="t">no</text>

  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,498 L730,510" class="arrow" style="opacity:0"/>
  <path d="M730,498 L730,498" class="arrow" style="opacity:0"/>
  <path d="M730,498 L730,498" class="arrow" style="opacity:0"/>

  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,498 L730,498" class="arrow" style="opacity:0"/>

  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,498 L730,498" class="arrow" style="opacity:0"/>

  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,498 L730,498" class="arrow" style="opacity:0"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <!-- response arrow -->
  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,432 L730,454" class="arrow"/>
  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <path d="M730,432 L730,454" class="arrow"/>

  <!-- loop back from tool runtime to prompt assembly -->
  <path d="M600,317 L560,317" class="arrow"/>
  <path d="M600,317 C520,250 520,250 450,250 C380,250 380,260 380,282" class="arrow"/>

  <!-- post to response -->
  <path d="M730,432 L730,454" class="arrow"/>
</svg>
""".strip()
    ),
    "fig:graph": _svg_wrap(
        r"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 260" role="img" aria-label="Graph of AASUs diagram">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">
      <path d="M0,0 L12,4 L0,8 Z" fill="#343a40" />
    </marker>
  </defs>
  <style>
    .box { fill: #f8f9fa; stroke: #343a40; stroke-width: 1.4; }
    .node { fill: #e7f5ff; stroke: #1c7ed6; stroke-width: 1.4; }
    .t { font: 14px "Times New Roman", Times, serif; fill: #111; }
    .tB { font: 600 14px "Times New Roman", Times, serif; fill: #111; }
    .arrow { stroke: #343a40; stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
  </style>

  <rect x="40" y="104" width="140" height="48" rx="10" ry="10" class="box"/>
  <text x="110" y="133" text-anchor="middle" class="tB">User</text>

  <rect x="240" y="104" width="160" height="48" rx="10" ry="10" class="box"/>
  <text x="320" y="133" text-anchor="middle" class="tB">Router</text>

  <rect x="470" y="44" width="170" height="48" rx="10" ry="10" class="node"/>
  <text x="555" y="73" text-anchor="middle" class="tB">AASU-1</text>

  <rect x="470" y="164" width="170" height="48" rx="10" ry="10" class="node"/>
  <text x="555" y="193" text-anchor="middle" class="tB">AASU-2</text>

  <rect x="690" y="104" width="170" height="48" rx="10" ry="10" class="node"/>
  <text x="775" y="133" text-anchor="middle" class="tB">AASU-3</text>

  <path d="M180,128 L240,128" class="arrow"/>
  <path d="M400,128 L470,68" class="arrow"/>
  <path d="M400,128 L470,188" class="arrow"/>
  <path d="M640,68 L690,128" class="arrow"/>
  <path d="M640,188 L690,128" class="arrow"/>
</svg>
""".strip()
    ),
    "fig:trust": _svg_wrap(
        r"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 240" role="img" aria-label="Trust boundaries diagram">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">
      <path d="M0,0 L12,4 L0,8 Z" fill="#343a40" />
    </marker>
  </defs>
  <style>
    .box { fill: #f8f9fa; stroke: #343a40; stroke-width: 1.4; }
    .svc { fill: #e7f5ff; stroke: #1c7ed6; stroke-width: 1.4; }
    .data { fill: #ebfbee; stroke: #2f9e44; stroke-width: 1.4; }
    .t { font: 13px "Times New Roman", Times, serif; fill: #111; }
    .tB { font: 600 13px "Times New Roman", Times, serif; fill: #111; }
    .arrow { stroke: #343a40; stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
    .tb { font: 12px "Times New Roman", Times, serif; fill: #555; }
  </style>

  <rect x="40" y="94" width="140" height="48" rx="10" ry="10" class="box"/>
  <text x="110" y="123" text-anchor="middle" class="tB">User</text>

  <rect x="220" y="94" width="170" height="48" rx="10" ry="10" class="svc"/>
  <text x="305" y="123" text-anchor="middle" class="tB">Application</text>

  <rect x="430" y="94" width="210" height="48" rx="10" ry="10" class="svc"/>
  <text x="535" y="123" text-anchor="middle" class="tB">Orchestrator</text>

  <rect x="690" y="22" width="180" height="48" rx="10" ry="10" class="box"/>
  <text x="780" y="51" text-anchor="middle" class="tB">Model provider</text>

  <rect x="690" y="94" width="180" height="48" rx="10" ry="10" class="data"/>
  <text x="780" y="123" text-anchor="middle" class="tB">Data stores</text>

  <rect x="690" y="166" width="180" height="48" rx="10" ry="10" class="box"/>
  <text x="780" y="195" text-anchor="middle" class="tB">Tool runtime</text>

  <path d="M180,118 L220,118" class="arrow"/>
  <text x="200" y="106" class="tb">TB1</text>

  <path d="M390,118 L430,118" class="arrow"/>
  <path d="M640,118 L690,46" class="arrow"/>
  <text x="650" y="64" class="tb">TB2</text>

  <path d="M640,118 L690,118" class="arrow"/>
  <text x="650" y="110" class="tb">TB4</text>

  <path d="M640,118 L690,190" class="arrow"/>
  <text x="650" y="170" class="tb">TB3</text>
</svg>
""".strip()
    ),
    "fig:layers": _svg_wrap(
        r"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 220" role="img" aria-label="Three-layer validation diagram">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">
      <path d="M0,0 L12,4 L0,8 Z" fill="#343a40" />
    </marker>
  </defs>
  <style>
    .box { fill: #f8f9fa; stroke: #343a40; stroke-width: 1.4; }
    .tB { font: 600 14px "Times New Roman", Times, serif; fill: #111; }
    .t { font: 13px "Times New Roman", Times, serif; fill: #111; }
    .arrow { stroke: #343a40; stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
  </style>

  <rect x="70" y="22" width="760" height="50" rx="10" ry="10" class="box"/>
  <text x="450" y="43" text-anchor="middle" class="tB">Layer 1 — AASU-level testing</text>
  <text x="450" y="61" text-anchor="middle" class="t">(nodes / configuration snapshots)</text>

  <rect x="70" y="86" width="760" height="50" rx="10" ry="10" class="box"/>
  <text x="450" y="107" text-anchor="middle" class="tB">Layer 2 — Orchestration testing</text>
  <text x="450" y="125" text-anchor="middle" class="t">(edges / propagation / routing)</text>

  <rect x="70" y="150" width="760" height="50" rx="10" ry="10" class="box"/>
  <text x="450" y="171" text-anchor="middle" class="tB">Layer 3 — Attack-graph testing</text>
  <text x="450" y="189" text-anchor="middle" class="t">(paths / topology / privilege pivots)</text>

  <path d="M450,72 L450,86" class="arrow"/>
  <path d="M450,136 L450,150" class="arrow"/>
</svg>
""".strip()
    ),
    "fig:lifecycle": _svg_wrap(
        r"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 240" role="img" aria-label="Governance lifecycle diagram">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">
      <path d="M0,0 L12,4 L0,8 Z" fill="#343a40" />
    </marker>
  </defs>
  <style>
    .box { fill: #f8f9fa; stroke: #343a40; stroke-width: 1.4; }
    .tB { font: 600 12.5px "Times New Roman", Times, serif; fill: #111; }
    .arrow { stroke: #343a40; stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
    .lbl { font: 12px "Times New Roman", Times, serif; fill: #555; }
  </style>

  <rect x="30" y="86" width="130" height="54" rx="10" ry="10" class="box"/>
  <text x="95" y="110" text-anchor="middle" class="tB">Define / update</text>
  <text x="95" y="128" text-anchor="middle" class="tB">P,M,R,T,K + H,S</text>

  <rect x="180" y="86" width="130" height="54" rx="10" ry="10" class="box"/>
  <text x="245" y="110" text-anchor="middle" class="tB">Generate</text>
  <text x="245" y="128" text-anchor="middle" class="tB">manifest</text>

  <rect x="330" y="86" width="130" height="54" rx="10" ry="10" class="box"/>
  <text x="395" y="110" text-anchor="middle" class="tB">Compute</text>
  <text x="395" y="128" text-anchor="middle" class="tB">AASU_ID</text>

  <rect x="480" y="86" width="130" height="54" rx="10" ry="10" class="box"/>
  <text x="545" y="110" text-anchor="middle" class="tB">Run layered</text>
  <text x="545" y="128" text-anchor="middle" class="tB">tests</text>

  <rect x="630" y="86" width="130" height="54" rx="10" ry="10" class="box"/>
  <text x="695" y="110" text-anchor="middle" class="tB">Risk review</text>
  <text x="695" y="128" text-anchor="middle" class="tB">&amp; sign-off</text>

  <rect x="780" y="86" width="130" height="54" rx="10" ry="10" class="box"/>
  <text x="845" y="110" text-anchor="middle" class="tB">Deploy</text>
  <text x="845" y="128" text-anchor="middle" class="tB">snapshot</text>

  <rect x="930" y="86" width="20" height="54" rx="10" ry="10" class="box" opacity="0"/>

  <rect x="780" y="168" width="130" height="54" rx="10" ry="10" class="box"/>
  <text x="845" y="192" text-anchor="middle" class="tB">Monitor</text>
  <text x="845" y="210" text-anchor="middle" class="tB">&amp; evidence</text>

  <path d="M160,113 L180,113" class="arrow"/>
  <path d="M310,113 L330,113" class="arrow"/>
  <path d="M460,113 L480,113" class="arrow"/>
  <path d="M610,113 L630,113" class="arrow"/>
  <path d="M760,113 L780,113" class="arrow"/>

  <path d="M845,140 L845,168" class="arrow"/>

  <path d="M780,195 C540,235 250,235 95,140" class="arrow"/>
  <text x="460" y="232" text-anchor="middle" class="lbl">change</text>
</svg>
""".strip()
    ),
}


def insert_before_closing_head(html: str, injection: str) -> str:
    if "</head>" not in html:
        raise RuntimeError("Expected standalone HTML with </head>.")
    return html.replace("</head>", f"{injection}\n</head>", 1)


def insert_diagram(html: str, fig_id: str, diagram_html: str) -> str:
    pattern = re.compile(rf'(<figure id="{re.escape(fig_id)}">\s*)(<figcaption)', re.MULTILINE)
    if not pattern.search(html):
        raise RuntimeError(f'Could not find figure id="{fig_id}" in HTML.')

    def _repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{diagram_html}\n{match.group(2)}"

    return pattern.sub(_repl, html, count=1)


def ensure_references_heading(html: str) -> str:
    if 'id="refs"' not in html:
        return html
    if re.search(r"<h[1-6][^>]*>\s*References\s*</h[1-6]>", html, re.IGNORECASE):
        return html
    return re.sub(
        r"(<div\s+id=\"refs\")",
        r'<h1 id="references">References</h1>\n\1',
        html,
        count=1,
        flags=re.MULTILINE | re.IGNORECASE,
    )


def build_html(tex_path: Path, bib_path: Path, html_out: Path) -> None:
    cmd = [
        "pandoc",
        str(tex_path),
        "-s",
        "--citeproc",
        "--mathml",
        f"--bibliography={bib_path}",
        "-o",
        str(html_out),
    ]
    subprocess.run(cmd, check=True)


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    footer_template = """
<div style="font-size:9px; width:100%; text-align:center; color:#666; padding:0 0.4in;">
  <span class="pageNumber"></span> / <span class="totalPages"></span>
</div>
""".strip()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1600})
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(pdf_path),
            format="Letter",
            margin={"top": "1in", "bottom": "1in", "left": "1in", "right": "1in"},
            print_background=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=footer_template,
        )
        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PDF via pandoc + Playwright (no TeX toolchain required).")
    parser.add_argument("--tex", default="main.tex", help="Input LaTeX file (default: main.tex)")
    parser.add_argument("--bib", default="references.bib", help="Input BibTeX file (default: references.bib)")
    parser.add_argument("--out", default="main.pdf", help="Output PDF path (default: main.pdf)")
    parser.add_argument("--keep-html", action="store_true", help="Keep the intermediate HTML next to the PDF")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    tex_path = (base_dir / args.tex).resolve()
    bib_path = (base_dir / args.bib).resolve()
    pdf_path = (base_dir / args.out).resolve()

    if not tex_path.exists():
        raise SystemExit(f"Missing TeX input: {tex_path}")
    if not bib_path.exists():
        raise SystemExit(f"Missing BibTeX input: {bib_path}")

    tmp_html = pdf_path.with_suffix(".html")
    build_html(tex_path=tex_path, bib_path=bib_path, html_out=tmp_html)

    html = tmp_html.read_text(encoding="utf-8")
    html = insert_before_closing_head(html, f"<style>\n{PRINT_CSS}\n</style>")
    html = ensure_references_heading(html)

    for fig_id, diagram in SVG_BY_FIGURE_ID.items():
        html = insert_diagram(html, fig_id=fig_id, diagram_html=diagram)

    tmp_html.write_text(html, encoding="utf-8")
    render_pdf(html_path=tmp_html, pdf_path=pdf_path)

    if not args.keep_html:
        tmp_html.unlink(missing_ok=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
