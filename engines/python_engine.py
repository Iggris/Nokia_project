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
            # Find all overlapping matches by starting search from each position
            pos = 0
            while pos < len(text):
                match = pattern_info['pattern'].search(text, pos)
                if match:
                    callback(
                        pattern_info['id'],  
                        match.start(),        
                        match.end(),         
                        0,            # flags        
                        None                  
                    )
                    # Move forward by 1 to find overlapping matches
                    pos = match.start() + 1
                else:
                    break
    def scan_stream(self, data_chunks: Iterable[bytes], callback: Callable, context: Any = None) -> None:
        """
        Scan data in streaming mode, processing each chunk individually.
        Uses an overlap buffer to catch matches that span chunk boundaries.
        """
        if not self.compiled_patterns:
            raise RuntimeError('Patterns Database is not compiled')
        
        # Buffer to store overlap from previous chunk
        overlap_buffer = b''
        total_offset = 0
        
        # Maximum pattern length to determine overlap size
        max_pattern_length = max(
            (len(p['original']) for p in self.compiled_patterns),
            default=100
        )
        overlap_size = max(max_pattern_length * 2, 1000)
        
        for chunk in data_chunks:
            # Combine overlap from previous chunk with current chunk
            combined = overlap_buffer + chunk
            
            try:
                text = combined.decode('utf-8', errors='ignore')
            except Exception:
                text = str(combined)
            
            # Determine the offset adjustment for this chunk
            chunk_start_offset = total_offset - len(overlap_buffer)
            
            # Scan the combined text
            for pattern_info in self.compiled_patterns:
                # Find all overlapping matches by starting search from each position
                pos = 0
                while pos < len(text):
                    match = pattern_info['pattern'].search(text, pos)
                    if match:
                        # Adjust match positions to global offsets
                        match_start = chunk_start_offset + match.start()
                        match_end = chunk_start_offset + match.end()
                        
                        # Only report matches that are in the "new" part of the chunk
                        # (not in the overlap region, to avoid duplicates)
                        if match.start() >= len(overlap_buffer) or total_offset == 0:
                            callback(
                                pattern_info['id'],
                                match_start,
                                match_end,
                                0,  # flags
                                context
                            )
                        # Move forward by 1 to find overlapping matches
                        pos = match.start() + 1
                    else:
                        break
            
            # Update offset and prepare overlap for next iteration
            total_offset += len(chunk)
            
            # Keep the last part of the chunk as overlap for next iteration
            if len(combined) > overlap_size:
                overlap_buffer = combined[-overlap_size:]
            else:
                overlap_buffer = combined