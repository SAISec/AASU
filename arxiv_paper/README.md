# AASU arXiv Paper (LaTeX Source)

This folder contains a submission-style LaTeX paper for the **Atomic AI Security Unit (AASU)** framework.

## Files

- `main.tex` — paper source
- `references.bib` — BibTeX bibliography

## Build (local)

If you have a TeX distribution installed (recommended: `latexmk`):

```bash
latexmk -pdf main.tex
```

If you don't have `latexmk`, a manual build usually works:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Build (no TeX toolchain)

If you don't have LaTeX installed, you can still generate a PDF using `pandoc` + Playwright (Chromium):

```bash
python3 build_pdf_playwright.py
```

This writes `main.pdf`. Add `--keep-html` to keep the intermediate `main.html`.
