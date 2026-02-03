"""
Generuje większe pliki danych dla testów ~1s skanowania.
Stream mode - można użyć dużych plików bo czytane są chunkami.
"""

import os
import random
import string

def generate_random_data(path: str, size_mb: int, seed: int = 42):
    random.seed(seed)
    target = size_mb * 1024 * 1024
    block_size = 1024 * 1024  # 1MB
    chars = string.ascii_letters + string.digits + " \n"
    
    print(f"Generuję {size_mb}MB -> {path} ...", end=" ", flush=True)
    
    with open(path, "wb") as f:
        written = 0
        while written < target:
            chunk_size = min(block_size, target - written)
            chunk = ''.join(random.choices(chars, k=chunk_size)).encode('ascii')
            f.write(chunk)
            written += len(chunk)
    
    print("OK")

def main():
    os.makedirs("data", exist_ok=True)
    
    # Większe pliki dla testów ~1s
    sizes = [300, 500, 800, 1000]
    
    for size in sizes:
        path = f"data/data_{size}mb.bin"
        if os.path.exists(path):
            print(f"Plik {path} już istnieje, pomijam")
        else:
            generate_random_data(path, size)
    
    print("\nGotowe! Wygenerowane pliki:")
    for size in sizes:
        path = f"data/data_{size}mb.bin"
        if os.path.exists(path):
            actual = os.path.getsize(path) / 1024 / 1024
            print(f"  {path}: {actual:.0f}MB")

if __name__ == "__main__":
    main()