"""
Memory layer for Personal Research Analyst.
Handles durable storage and retrieval of user preferences and facts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas import MemoryRecord


class MemoryLayer:
    """Manages durable memory persistence across runs."""
    
    def __init__(self, memory_file: str = "state/memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._memory: Dict[str, MemoryRecord] = {}
        self._load()
    
    def _load(self) -> None:
        """Load memory from disk."""
        if self.memory_file.exists():
            try:
                data = json.loads(self.memory_file.read_text(encoding="utf-8"))
                for key, record_data in data.items():
                    self._memory[key] = MemoryRecord(**record_data)
            except (json.JSONDecodeError, OSError):
                self._memory = {}
    
    def _save(self) -> None:
        """Save memory to disk."""
        data = {
            key: record.model_dump(mode='json')
            for key, record in self._memory.items()
        }
        self.memory_file.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8"
        )
    
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve a value from memory by key.
        
        Args:
            key: The memory key to look up
            
        Returns:
            The value if found, None otherwise
        """
        record = self._memory.get(key)
        if record:
            # Update access tracking
            record.accessed_at = datetime.now()
            record.access_count += 1
            self._save()
            return record.value
        return None
    
    def set(self, key: str, value: str) -> None:
        """
        Store a value in memory.
        
        Args:
            key: The memory key
            value: The value to store
        """
        now = datetime.now()
        if key in self._memory:
            # Update existing record
            record = self._memory[key]
            record.value = value
            record.accessed_at = now
            record.access_count += 1
        else:
            # Create new record
            self._memory[key] = MemoryRecord(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now
            )
        self._save()
    
    def search(self, query: str) -> List[MemoryRecord]:
        """
        Search memory for records containing the query in key or value.
        
        Args:
            query: Search term
            
        Returns:
            List of matching memory records, sorted by relevance
        """
        query_lower = query.lower()
        matches = []
        
        for record in self._memory.values():
            score = 0
            if query_lower in record.key.lower():
                score += 2  # Key matches are more relevant
            if query_lower in record.value.lower():
                score += 1
            if score > 0:
                matches.append((score, record))
        
        # Sort by score descending, then by access count descending
        matches.sort(key=lambda x: (-x[0], -x[1].access_count))
        return [record for _, record in matches]
    
    def read_all(self) -> List[MemoryRecord]:
        """
        Read all memory records.
        
        Returns:
            List of all memory records
        """
        return list(self._memory.values())
    
    def clear(self) -> None:
        """Clear all memory (useful for testing)."""
        self._memory.clear()
        self._save()