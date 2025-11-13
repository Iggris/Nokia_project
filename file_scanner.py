import os
from typing import List, Dict
from engines.base_engine import RegexEngine  
from engines.hs_engine import HyperscanEngine 

class FileScanner:
    """Klasa do skanowania plików z użyciem różnych silników regex"""
    
    def __init__(self, engine: RegexEngine = None):
        """
        Args:
            engine: Implementacja RegexEngine (domyślnie HyperscanEngine)
        """
        self.engine = engine or HyperscanEngine()
        self.results = []
    
    def compile_patterns(self, patterns: List[str]) -> None:
        """Kompiluje wzorce jako bytes"""
        pattern_bytes = [pattern.encode('utf-8') for pattern in patterns]
        self.engine.compile_patterns(pattern_bytes)
    
    def _match_callback(self, pattern_id: int, start: int, end: int, flags: int, filename: str):
        """Callback wywoływany przy znalezieniu dopasowania
        
        
        """
        pattern = self.engine.patterns[pattern_id]
        actual_start = end - len(pattern)
        
        result = {
            'pattern_id': pattern_id,
            'start': actual_start,
            'end': end,
            'match': pattern.decode('utf-8', errors='ignore'),
            'filename': filename
        }
        self.results.append(result)
        print(f"Znaleziono '{result['match']}' (wzorzec {pattern_id}) w {filename} na pozycji {actual_start}-{end}")
    
    def scan_file(self, filename: str, chunk_size: int = 4096) -> List[Dict]:
        """Skanuje plik w trybie strumieniowym (STREAM mode)
        
        Args:
            filename: Ścieżka do pliku
            chunk_size: Rozmiar chunka w bajtach (domyślnie 4096)
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Plik {filename} nie istnieje")
        
        self.results = []
        
        def callback(pattern_id, start, end, flags, context):
            self._match_callback(pattern_id, start, end, flags, filename)
        
        try:
            # Czytaj plik w chunkach
            print(f"Skanowanie strumieniowe (chunk_size={chunk_size} bajtów)")
            chunks = []
            total_bytes = 0
            
            with open(filename, 'rb') as file:
                chunk_number = 0
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    
                    chunk_number += 1
                    total_bytes += len(chunk)
                    print(f"  Chunk {chunk_number}: {len(chunk)} bajtów")
                    chunks.append(chunk)
            
            # Przekaż wszystkie chunki do silnika strumieniowego
            # Hyperscan Stream pamięta stan między chunkami!
            self.engine.scan_stream(chunks, callback, context=filename)
            
            print(f"  Zakończono skanowanie: {chunk_number} chunków, {total_bytes} bajtów")
            
            return self.results
            
        except Exception as e:
            print(f"Błąd podczas skanowania pliku {filename}: {e}")
            raise