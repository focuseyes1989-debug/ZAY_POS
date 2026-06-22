# models/database/profiler.py
"""
Query profiling and performance monitoring.
"""

import time
import functools
from loguru import logger
from collections import defaultdict
from datetime import datetime, timedelta

class QueryProfiler:
    """Track and profile database queries."""
    
    def __init__(self):
        self.queries = []
        self.slow_queries = []
        self.threshold = 0.5  # 500ms
    
    def profile(self, func):
        """Decorator to profile a query function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Record query
            query_info = {
                'function': func.__name__,
                'args': args,
                'duration': duration,
                'timestamp': datetime.now()
            }
            self.queries.append(query_info)
            
            # Track slow queries
            if duration > self.threshold:
                self.slow_queries.append(query_info)
                logger.warning(f"Slow query: {func.__name__} took {duration:.3f}s")
            
            return result
        return wrapper
    
    def get_stats(self, last_minutes=5):
        """Get query statistics for last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=last_minutes)
        
        recent_queries = [
            q for q in self.queries 
            if q['timestamp'] > cutoff
        ]
        
        if not recent_queries:
            return None
        
        total_queries = len(recent_queries)
        total_time = sum(q['duration'] for q in recent_queries)
        avg_time = total_time / total_queries if total_queries > 0 else 0
        
        # Group by function
        by_function = defaultdict(list)
        for q in recent_queries:
            by_function[q['function']].append(q['duration'])
        
        function_stats = {}
        for name, durations in by_function.items():
            function_stats[name] = {
                'count': len(durations),
                'avg': sum(durations) / len(durations),
                'max': max(durations),
                'min': min(durations)
            }
        
        return {
            'total_queries': total_queries,
            'total_time': total_time,
            'avg_time': avg_time,
            'slow_queries': len(self.slow_queries),
            'by_function': function_stats
        }
    
    def clear(self):
        """Clear all recorded queries."""
        self.queries.clear()
        self.slow_queries.clear()


# Global profiler instance
_query_profiler = QueryProfiler()


def profile_query(func):
    """Decorator for profiling queries."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return _query_profiler.profile(func)(*args, **kwargs)
    return wrapper