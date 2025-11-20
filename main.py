import sys
import os
from file_regex.file_regex import FileRegex
import file_scanner

# Dodanie ścieżki do modułów
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():

    if len(sys.argv) < 2:
        print("Użycie: python main.py <plik_do_skanowania>")
        sys.exit(1)
    
    filename = sys.argv[1]
    fr = FileRegex()
    
    # Wzorce do wyszukania
    patterns = fr.elements()
    
    # Inicjalizacja skanera - użyj pełnej ścieżki
    scanner = file_scanner.FileScanner()
    scanner.compile_patterns(patterns)

    print(f"Skanowanie pliku: {filename}")
    print(f"Wzorce: {patterns}")
    print("-" * 50)
    
    # Skanowanie pliku w trybie strumieniowym (Hyperscan STREAM mode)
    results = scanner.scan_file(filename, chunk_size=4096)
    for result in results:
        print(f"Znaleziono '{result['match']}' (wzorzec {result['pattern_id']}) w {filename} na pozycji {result['start']}-{result['end']}")
    cataloge = scanner.scan_tree("/home/igris/Desktop/test")
    print("-" * 50)
    print(f"Znaleziono {len(results)} dopasowań")
    print(f"Znaleziono {len(cataloge)} dopasowań w drzewie katalogów:")
    for match in cataloge:
        print(match)

    print("\nSerializing and deserializing patterns database:\n")

    scanner.engine.save_db("hs.db")
    scanner2 = file_scanner.FileScanner()
    scanner2.engine.load_db("hs.db")

    results2 = scanner2.scan_file(filename, chunk_size=4096)
    for result in results2:
        print(f"Znaleziono '{result['match']}' (wzorzec {result['pattern_id']}) w {filename} na pozycji {result['start']}-{result['end']}")
    print("-" * 50)
    print(f"Znaleziono {len(results2)} dopasowań")

    return results


if __name__ == "__main__":
    main()
