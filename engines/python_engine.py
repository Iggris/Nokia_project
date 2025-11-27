import re
from .base_engine import RegexEngine
from typing import List, Callable, Any, Iterable


class PythonEngine(RegexEngine):
    
    def __init__(self):
        self.compiled_patterns = []
        self.patterns = []
    
    def compile_patterns(self, patterns: List[bytes], ids: List[int] = None) -> None:
        self.patterns = patterns
        self.compiled_patterns = []
        
        if ids is None:
            ids = list(range(len(patterns)))
        
        for pattern_id, pattern_bytes in zip(ids, patterns):
            try:
                pattern_str = pattern_bytes.decode('utf-8')
                compiled = re.compile(pattern_str)
                self.compiled_patterns.append({
                    'id': pattern_id,
                    'pattern': compiled,
                    'original': pattern_bytes
                })
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{pattern_bytes}': {e}")
    
    def scan(self, data: bytes, callback: Callable) -> None:
        
        if not self.compiled_patterns:
            raise RuntimeError('Patterns Database is not compiled')
        
        try:
            text = data.decode('utf-8', errors='ignore')
        except Exception:
            text = str(data)
    
        for pattern_info in self.compiled_patterns:
            for match in pattern_info['pattern'].finditer(text):
               
                callback(
                    pattern_info['id'],  
                    match.start(),        
                    match.end(),         
                    0,            # flags        
                    None                  
                )
    # stream jest oszukany - buforujemy wszystko i skanujemy na raz
    def scan_stream(self, data_chunks: Iterable[bytes], callback: Callable, context: Any = None) -> None:
       
        if not self.compiled_patterns:
            raise RuntimeError('Patterns Database is not compiled')
        

        buffer = b''
        for chunk in data_chunks:
            buffer += chunk
        
        try:
            text = buffer.decode('utf-8', errors='ignore')
        except Exception:
            text = str(buffer)
        
       
        for pattern_info in self.compiled_patterns:
            for match in pattern_info['pattern'].finditer(text):
                
                callback(
                    pattern_info['id'], 
                    match.start(),       
                    match.end(),        
                    0,                    # flags
                    context               
                )