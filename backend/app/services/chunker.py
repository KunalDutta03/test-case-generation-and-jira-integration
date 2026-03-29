"""
Token-aware text chunker with overlap.
Default: 512 tokens per chunk, 64 token overlap.
"""
import tiktoken

TOKENIZER = tiktoken.get_encoding("cl100k_base")


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64
) -> list[dict]:
    """
    Split text into overlapping chunks.
    Returns list of {content, token_count, chunk_index}.
    """
    tokens = TOKENIZER.encode(text)
    chunks = []
    start = 0
    index = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = TOKENIZER.decode(chunk_tokens)
        chunks.append({
            "content": chunk_text_str,
            "token_count": len(chunk_tokens),
            "chunk_index": index,
        })
        index += 1
        if end == len(tokens):
            break
        start = end - overlap

    return chunks
