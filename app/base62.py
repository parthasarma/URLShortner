ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)

def encode(n: int) -> str:
    if n < 1:
        raise ValueError("id must be >= 1")
    s = []
    while n:
        n, rem = divmod(n, BASE)
        s.append(ALPHABET[rem])
    return "".join(reversed(s))

def decode(s: str) -> int:
    if not s:
        raise ValueError("empty code")
    n = 0
    for c in s:
        try:
            val = ALPHABET.index(c)
        except ValueError:
            raise ValueError("invalid char in code")
        n = n * BASE + val
    if n < 1:
        raise ValueError("decoded id must be >= 1")
    return n
