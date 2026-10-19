# Clean Pages

Turn books and PDFs into clean text files AI can actually read.

## The problem

Books and PDFs come packed with clutter — copyright pages, tables of contents, indexes, glossaries, about-the-author sections. That noise makes up nearly half the file and gets in the way when you're trying to feed documents into an AI system. Most conversion tools dump everything in, producing bloated output that's hard to work with.

## What Clean Pages does

Clean Pages strips everything except the actual narrative content. It converts EPUB and PDF files into clean Markdown that's 40–60% smaller and ready for AI ingestion, RAG pipelines, and document workflows. No templates to maintain, no cloud services, no complicated setup.

## Who it's for

Anyone building AI-powered document systems — knowledge bases, customer support bots, internal research tools — who needs clean, chunkable text from books and documents without the overhead.

## Privacy & security

- **100% local** — zero data leaves your machine
- **No cloud APIs, no API keys, no accounts required**
- Pure Python — no pandoc, no poppler, no system dependencies to install
- Your documents never touch a server

## How to use

```bash
# Convert a single book
uv run clean-pages document.epub
# → document.md (clean narrative content only)

# Convert a PDF
uv run clean-pages document.pdf

# Convert a whole folder
uv run clean-pages ./books/ --output ./my-documents/
```

## License

MIT. Local-first document conversion — your files stay on your machine.
