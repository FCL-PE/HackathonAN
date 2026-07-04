"""
extraction.py
Découpe un PDF de rapport/loi en chunks exploitables par un LLM.

Usage:
    from extraction import extract_chunks
    chunks = extract_chunks("mon_rapport.pdf")
"""

from __future__ import annotations

import fitz  # PyMuPDF
from dataclasses import dataclass


@dataclass
class Chunk:
    id: int
    text: str
    page_start: int
    page_end: int


def extract_chunks(pdf_path: str, max_chars: int = 6000, overlap_chars: int = 500) -> list[Chunk]:
    """
    Extrait le texte d'un PDF et le découpe en chunks avec overlap,
    en gardant la trace des numéros de page (utile pour la traçabilité des sources).

    max_chars ~ 6000 caractères ~ 1500 tokens, une taille raisonnable
    pour un prompt de synthèse sans perdre le fil.
    """
    doc = fitz.open(pdf_path)

    # 1. On extrait le texte page par page, en gardant l'info de page
    pages_text = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages_text.append((page_num, text))
    doc.close()

    if not pages_text:
        raise ValueError(f"Aucun texte extrait de {pdf_path} — PDF scanné/image ? OCR nécessaire.")

    # 2. On concatène tout en gardant les frontières de page
    full_text = ""
    page_boundaries = []  # (char_index, page_num)
    for page_num, text in pages_text:
        page_boundaries.append((len(full_text), page_num))
        full_text += text + "\n"

    # 3. Découpage en chunks avec overlap
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(full_text):
        end = min(start + max_chars, len(full_text))
        chunk_text = full_text[start:end]

        # trouve les pages couvertes par ce chunk
        pages_in_chunk = [p for idx, p in page_boundaries if start <= idx < end]
        if not pages_in_chunk:
            pages_in_chunk = [page_boundaries[-1][1]]

        chunks.append(Chunk(
            id=chunk_id,
            text=chunk_text.strip(),
            page_start=min(pages_in_chunk),
            page_end=max(pages_in_chunk),
        ))
        chunk_id += 1
        start = end - overlap_chars if end < len(full_text) else end

    return chunks


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extraction.py <chemin_vers_pdf>")
        sys.exit(1)

    chunks = extract_chunks(sys.argv[1])
    print(f"{len(chunks)} chunks extraits.\n")
    for c in chunks[:3]:
        print(f"--- Chunk {c.id} (pages {c.page_start}-{c.page_end}) ---")
        print(c.text[:200] + "...\n")
