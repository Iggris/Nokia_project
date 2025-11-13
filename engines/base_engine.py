from abc import ABC, abstractmethod
from typing import List, Callable, Any

class RegexEngine(ABC):
    """Abstrakcyjna klasa bazowa dla silników regex"""
    
    @abstractmethod
    def compile_patterns(self, patterns: List[bytes], ids: List[int] = None) -> None:
        """Kompiluje wzorce regex"""
        pass
    
    @abstractmethod
    def scan(self, data: bytes, callback: Callable) -> None:
        """Skanuje dane i wywołuje callback przy dopasowaniu"""
        pass
    
    @abstractmethod
    def scan_stream(self, data_chunks: List[bytes], callback: Callable, context: Any = None) -> None:
        """Skanuje dane w trybie strumieniowym - przyjmuje listę chunków"""
        pass