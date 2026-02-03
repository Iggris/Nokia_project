import os
import random
import string
import argparse

def ensure_dirs():
    os.makedirs("patterns", exist_ok=True)
    os.makedirs("data", exist_ok=True)

def generate_simple_words(path: str, n: int, min_len: int = 4, max_len: int = 12, 
                          word_boundaries: bool = True, seed: int = 42):
    random.seed(seed)
    patterns = set()
    
    if n > 50000:
        base_chars = string.ascii_lowercase
        generated = 0
        length = min_len
        
        while generated < n:
            for combo in _generate_combos(base_chars, length, n - generated):
                if word_boundaries:
                    patterns.add(f"\\b{combo}\\b")
                else:
                    patterns.add(combo)
                generated += 1
                if generated >= n:
                    break
            length += 1
            if length > max_len:
                length = min_len
                base_chars = ''.join(random.choices(string.ascii_lowercase, k=2)) + string.ascii_lowercase
    else:
        attempts = 0
        while len(patterns) < n and attempts < n * 10:
            length = random.randint(min_len, max_len)
            word = ''.join(random.choices(string.ascii_lowercase, k=length))
            if word_boundaries:
                patterns.add(f"\\b{word}\\b")
            else:
                patterns.add(word)
            attempts += 1
    
    with open(path, "w", encoding="utf-8") as f:
        for p in list(patterns)[:n]:
            f.write(p + "\n")
    
    est_ram = n * 400 / 1024 / 1024
    print(f"[OK] {n} prostych wzorców -> {path} (est. RAM: ~{est_ram:.0f}MB)")

def _generate_combos(chars: str, length: int, limit: int):
    if length == 1:
        for c in chars:
            yield c
    else:
        count = 0
        for c in chars:
            for rest in _generate_combos(chars, length - 1, limit - count):
                yield c + rest
                count += 1
                if count >= limit:
                    return

def generate_bounded_patterns(path: str, n: int, gap: int):
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n):
            f.write(f"PAT{i:06d}.{{{gap},{gap}}}END{i:06d}\n")
    
    est_ram = n * gap * 8 / 1024 / 1024
    print(f"[OK] {n} bounded (gap={gap}) -> {path} (est. RAM: ~{est_ram:.0f}MB - MOŻE BYĆ WIĘCEJ!)")

def generate_bounded_patterns_varied(path: str, n: int, min_gap: int, max_gap: int, seed: int = 42):
    random.seed(seed)
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n):
            gap = random.randint(min_gap, max_gap)
            f.write(f"PAT{i:06d}.{{{gap},{gap}}}END{i:06d}\n")
    print(f"[OK] {n} bounded (gap={min_gap}-{max_gap}) -> {path}")

def generate_alternation_patterns(path: str, n_patterns: int, n_alts: int):
    with open(path, "w", encoding="utf-8") as f:
        for p in range(n_patterns):
            alts = [f"A{p:03d}_{i:06d}" for i in range(n_alts)]
            f.write("(" + "|".join(alts) + f")B{p:03d}\n")
    
    total_alts = n_patterns * n_alts
    est_ram = total_alts * 50 / 1024 / 1024
    print(f"[OK] {n_patterns} × {n_alts} alts -> {path} (est. RAM: ~{est_ram:.0f}MB)")

def generate_complex_patterns(path: str, n: int, seed: int = 42):
    random.seed(seed)
    templates = [
        lambda i: f"prefix{i:04d}[a-z]{{3,8}}suffix{i:04d}",
        lambda i: f"(type{i:04d}|kind{i:04d}|sort{i:04d})[0-9]+",
        lambda i: f"data{i:04d}(-[a-z]+)?-end",
        lambda i: f"[A-Z]{{{i % 3 + 1}}}[0-9]{{2,4}}[a-z]+",
        lambda i: f"\\bword{i:04d}\\b",
    ]
    
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n):
            template = random.choice(templates)
            f.write(template(i) + "\n")
    print(f"[OK] {n} złożonych wzorców -> {path}")

def generate_random_data(path: str, size_mb: int, seed: int = 42):
    random.seed(seed)
    target = size_mb * 1024 * 1024
    block_size = 1024 * 1024
    chars = string.ascii_letters + string.digits + " \n"
    
    with open(path, "wb") as f:
        written = 0
        while written < target:
            chunk_size = min(block_size, target - written)
            chunk = ''.join(random.choices(chars, k=chunk_size)).encode('ascii')
            f.write(chunk)
            written += len(chunk)
    print(f"[OK] {size_mb}MB danych -> {path}")

def generate_bounded_data(path: str, size_mb: int, n_patterns: int, gap: int, 
                          match_every: int = 0, seed: int = 42):
    random.seed(seed)
    target = size_mb * 1024 * 1024
    out = bytearray()
    block = 0
    
    while len(out) < target:
        idx = random.randrange(n_patterns)
        head = f"PAT{idx:06d}".encode()
        tail_ok = f"END{idx:06d}".encode()
        tail_bad = f"ENX{idx:06d}".encode()
        
        out += head
        out += b"a" * gap
        if match_every > 0 and (block % match_every == 0):
            out += tail_ok
        else:
            out += tail_bad
        out += b" "
        block += 1
    
    with open(path, "wb") as f:
        f.write(out[:target])
    matches = "brak" if match_every == 0 else f"co {match_every}"
    print(f"[OK] {size_mb}MB bounded data ({matches} dopasowań) -> {path}")

def generate_all_patterns_6gb():
    ensure_dirs()
    
    print("\n PROSTE WZORCE")
    generate_simple_words("patterns/simple_10k.txt", 10000)
    generate_simple_words("patterns/simple_25k.txt", 25000)
    generate_simple_words("patterns/simple_50k.txt", 50000)
    generate_simple_words("patterns/simple_75k.txt", 75000)
    generate_simple_words("patterns/simple_100k.txt", 100000)
    
    print("\n BOUNDED PATTERNS ")
    generate_bounded_patterns("patterns/bounded_500_gap100.txt", 500, 100)
    generate_bounded_patterns("patterns/bounded_500_gap200.txt", 500, 200)
    generate_bounded_patterns("patterns/bounded_300_gap300.txt", 300, 300)
    generate_bounded_patterns("patterns/bounded_200_gap500.txt", 200, 500)
    generate_bounded_patterns("patterns/bounded_100_gap1000.txt", 100, 1000)
    generate_bounded_patterns_varied("patterns/bounded_300_varied.txt", 300, 50, 250)
    
    print("\n ALTERNATION PATTERNS")
    generate_alternation_patterns("patterns/alt_10_x_500.txt", 10, 500)
    generate_alternation_patterns("patterns/alt_25_x_500.txt", 25, 500)
    generate_alternation_patterns("patterns/alt_50_x_500.txt", 50, 500)
    generate_alternation_patterns("patterns/alt_50_x_1000.txt", 50, 1000)
    
    print("\n ZŁOŻONE WZORCE")
    generate_complex_patterns("patterns/complex_1k.txt", 1000)
    generate_complex_patterns("patterns/complex_5k.txt", 5000)
    generate_complex_patterns("patterns/complex_10k.txt", 10000)

def generate_all_data_6gb():
    ensure_dirs()
    
    print("\n DANE LOSOWE ")
    generate_random_data("data/data_50mb.bin", 50)
    generate_random_data("data/data_100mb.bin", 100)
    generate_random_data("data/data_150mb.bin", 150)
    generate_random_data("data/data_200mb.bin", 200)
    
    print("\n DANE DLA BOUNDED ")
    generate_bounded_data("data/bounded_50mb.bin", 50, 300, 300, match_every=0)
    generate_bounded_data("data/bounded_100mb.bin", 100, 300, 300, match_every=0)

def generate_all():
    generate_all_patterns_6gb()
    generate_all_data_6gb()

def main():
    parser = argparse.ArgumentParser(description="Generator dla Hyperscan (~6GB RAM)")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--patterns", action="store_true")
    parser.add_argument("--data", action="store_true")
    parser.add_argument("--simple", type=int, metavar="N")
    parser.add_argument("--bounded", nargs=2, type=int, metavar=("N", "GAP"))
    parser.add_argument("--alt", nargs=2, type=int, metavar=("PATTERNS", "ALTS"))
    parser.add_argument("--complex", type=int, metavar="N")
    parser.add_argument("--random-data", type=int, metavar="MB")
    parser.add_argument("--bounded-data", nargs=3, type=int, metavar=("MB", "N", "GAP"))
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--seed", type=int, default=42)
    
    args = parser.parse_args()
    ensure_dirs()
    
    if args.all:
        generate_all()
    elif args.patterns:
        generate_all_patterns_6gb()
    elif args.data:
        generate_all_data_6gb()
    elif args.simple:
        path = args.output or f"patterns/simple_{args.simple}.txt"
        generate_simple_words(path, args.simple, seed=args.seed)
    elif args.bounded:
        n, gap = args.bounded
        path = args.output or f"patterns/bounded_{n}_gap{gap}.txt"
        generate_bounded_patterns(path, n, gap)
    elif args.alt:
        patterns, alts = args.alt
        path = args.output or f"patterns/alt_{patterns}_x_{alts}.txt"
        generate_alternation_patterns(path, patterns, alts)
    elif args.complex:
        path = args.output or f"patterns/complex_{args.complex}.txt"
        generate_complex_patterns(path, args.complex, seed=args.seed)
    elif args.random_data:
        path = args.output or f"data/data_{args.random_data}mb.bin"
        generate_random_data(path, args.random_data, seed=args.seed)
    elif args.bounded_data:
        mb, n, gap = args.bounded_data
        path = args.output or f"data/bounded_{mb}mb.bin"
        generate_bounded_data(path, mb, n, gap, seed=args.seed)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()