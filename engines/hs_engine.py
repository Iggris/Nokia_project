import hyperscan
from .base_engine import RegexEngine
from typing import List, Callable, Any

class HyperscanEngine(RegexEngine):
    def __init__(self):
        self.db = None
        self.patterns = []
    
    def compile_patterns(self, patterns, ids=None):
        self.patterns = patterns
        if ids is None:
            ids = list(range(len(patterns)))
        flags = [hyperscan.HS_FLAG_CASELESS] * len(patterns)
        self.db = hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)
        self.db.compile(expressions=patterns, ids=ids, flags=flags, elements=len(patterns))
    
    def scan(self, data, callback):
        if self.db is None:
            raise RuntimeError('Wzorce nie zostaly skompilowane')
        self.db.scan(data, match_event_handler=callback)
    
    def scan_stream(self, data_chunks, callback, context=None):
        if self.db is None:
            raise RuntimeError('Wzorce nie zostaly skompilowane')
        full_data = b''.join(data_chunks)
        self.db.scan(full_data, match_event_handler=callback, context=context)
