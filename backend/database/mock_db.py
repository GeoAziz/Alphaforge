"""
Mock Database for testing without Supabase dependency.
Stores data in memory with persistence to JSON file.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class MockDatabase:
    """In-memory mock database for MVP testing."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize mock database with empty tables."""
        self.data_file = Path(__file__).parent.parent / "mock_data.json"
        self.tables = {
            "users": [],
            "signals": [],
            "paper_trades": [],
            "positions": [],
            "portfolios": [],
            "external_signals": [],
        }
        
        # Load from file if exists
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    self.tables = json.load(f)
                logger.info(f"✅ Mock database loaded from {self.data_file}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load mock data: {e}")
    
    def save(self):
        """Persist mock data to JSON file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.tables, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ Failed to save mock data: {e}")
    
    class Table:
        """Mock table interface."""
        
        def __init__(self, table_name: str, db: 'MockDatabase'):
            self.table_name = table_name
            self.db = db
        
        def insert(self, data: Dict[str, Any]):
            """Insert a single record."""
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow().isoformat()
            
            self.db.tables[self.table_name].append(data)
            self.db.save()
            
            return MockInsert([data])
        
        def select(self, *args):
            """Select from table."""
            return MockQuery(self.table_name, self.db, list(self.db.tables[self.table_name]))
        
        def update(self, data: Dict[str, Any]):
            """Update records."""
            return MockUpdate(self.table_name, self.db, data)

        def upsert(self, data: Dict[str, Any]):
            """Insert or update records."""
            return MockUpsert(self.table_name, self.db, data)
        
        def delete(self):
            """Delete records."""
            return MockDelete(self.table_name, self.db)
    
    def table(self, table_name: str):
        """Get table reference."""
        if table_name not in self.tables:
            self.tables[table_name] = []
        return self.Table(table_name, self)


class MockInsert:
    """Mock insert builder."""
    
    def __init__(self, records: List[Dict]):
        self.records = records
    
    def execute(self):
        """Execute insert."""
        return MockResponse(self.records)


class MockQuery:
    """Mock query builder."""
    
    def __init__(self, table_name: str, db: MockDatabase, records: List[Dict]):
        self.table_name = table_name
        self.db = db
        self.records = records
        self.filters = []
        self.limit_count = None
        self.range_start = None
        self.range_end = None
        self.order_field = None
        self.order_desc = False
    
    def eq(self, field: str, value: Any):
        """Filter by equality."""
        self.filters.append(("eq", field, value))
        return self

    def gte(self, field: str, value: Any):
        """Filter by greater than or equal."""
        self.filters.append(("gte", field, value))
        return self

    def lte(self, field: str, value: Any):
        """Filter by less than or equal."""
        self.filters.append(("lte", field, value))
        return self

    def gt(self, field: str, value: Any):
        """Filter by greater than."""
        self.filters.append(("gt", field, value))
        return self

    def lt(self, field: str, value: Any):
        """Filter by less than."""
        self.filters.append(("lt", field, value))
        return self

    def order(self, field: str, desc: bool = False):
        """Sort results by field."""
        self.order_field = field
        self.order_desc = desc
        return self
    
    def limit(self, count: int):
        """Limit results."""
        self.limit_count = count
        return self

    def range(self, start: int, end: int):
        """Slice results using inclusive start/end indices."""
        self.range_start = max(0, int(start))
        self.range_end = max(self.range_start, int(end))
        return self
    
    def execute(self):
        """Execute query."""
        filtered = list(self.records)

        for operator, field, value in self.filters:
            if operator == "eq":
                filtered = [record for record in filtered if record.get(field) == value]
            elif operator == "gte":
                filtered = [record for record in filtered if _safe_compare(record.get(field), value, ">=")]
            elif operator == "lte":
                filtered = [record for record in filtered if _safe_compare(record.get(field), value, "<=")]
            elif operator == "gt":
                filtered = [record for record in filtered if _safe_compare(record.get(field), value, ">")]
            elif operator == "lt":
                filtered = [record for record in filtered if _safe_compare(record.get(field), value, "<")]

        if self.order_field is not None:
            filtered = sorted(
                filtered,
                key=lambda record: _sortable_value(record.get(self.order_field)),
                reverse=self.order_desc,
            )

        if self.range_start is not None and self.range_end is not None:
            filtered = filtered[self.range_start:self.range_end + 1]
        
        if self.limit_count:
            filtered = filtered[:self.limit_count]
        
        return MockResponse(filtered)


class MockUpdate:
    """Mock update builder."""
    
    def __init__(self, table_name: str, db: MockDatabase, data: Dict):
        self.table_name = table_name
        self.db = db
        self.data = data
        self.filters = []
    
    def eq(self, field: str, value: Any):
        """Filter by equality."""
        self.filters.append((field, value))
        return self
    
    def execute(self):
        """Execute update."""
        data = self.data.copy()
        data["updated_at"] = datetime.utcnow().isoformat()
        
        updated = []
        for record in self.db.tables[self.table_name]:
            match = all(record.get(f) == v for f, v in self.filters)
            if match:
                record.update(data)
                updated.append(record)
        
        self.db.save()
        return MockResponse(updated)


class MockUpsert:
    """Mock upsert builder."""

    def __init__(self, table_name: str, db: MockDatabase, data: Dict):
        self.table_name = table_name
        self.db = db
        self.data = data

    def execute(self):
        """Execute upsert."""
        payload = self.data.copy()
        payload.setdefault("updated_at", datetime.utcnow().isoformat())

        if "id" in payload and payload["id"] is not None:
            target = next(
                (record for record in self.db.tables[self.table_name] if record.get("id") == payload["id"]),
                None,
            )
        elif payload.get("user_id") is not None and payload.get("exchange") is not None:
            target = next(
                (
                    record
                    for record in self.db.tables[self.table_name]
                    if record.get("user_id") == payload.get("user_id")
                    and record.get("exchange") == payload.get("exchange")
                ),
                None,
            )
        elif payload.get("user_id") is not None:
            target = next(
                (record for record in self.db.tables[self.table_name] if record.get("user_id") == payload.get("user_id")),
                None,
            )
        else:
            target = None

        if target is not None:
            target.update(payload)
            saved = target
        else:
            payload.setdefault("id", str(uuid.uuid4()))
            payload.setdefault("created_at", datetime.utcnow().isoformat())
            self.db.tables[self.table_name].append(payload)
            saved = payload

        self.db.save()
        return MockResponse([saved])


class MockDelete:
    """Mock delete builder."""
    
    def __init__(self, table_name: str, db: MockDatabase):
        self.table_name = table_name
        self.db = db
        self.filters = []
    
    def eq(self, field: str, value: Any):
        """Filter by equality."""
        self.filters.append((field, value))
        return self
    
    def execute(self):
        """Execute delete."""
        initial_count = len(self.db.tables[self.table_name])
        
        self.db.tables[self.table_name] = [
            r for r in self.db.tables[self.table_name]
            if not all(r.get(f) == v for f, v in self.filters)
        ]
        
        deleted_count = initial_count - len(self.db.tables[self.table_name])
        self.db.save()
        
        return MockResponse([], message=f"Deleted {deleted_count} records")


class MockResponse:
    """Mock API response."""
    
    def __init__(self, data: List[Dict] = None, message: str = ""):
        self.data = data or []
        self.message = message


def _safe_compare(left: Any, right: Any, operator: str) -> bool:
    """Compare values safely for mock filtering."""
    if left is None:
        return False

    left_value = _sortable_value(left)
    right_value = _sortable_value(right)

    if operator == ">=":
        return left_value >= right_value
    if operator == "<=":
        return left_value <= right_value
    if operator == ">":
        return left_value > right_value
    if operator == "<":
        return left_value < right_value
    return False


def _sortable_value(value: Any):
    """Normalize values to support ordering and comparisons."""
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value.lower()
    return value


class MockSupabaseClient:
    """Mock Supabase client."""
    
    def __init__(self):
        self.db = MockDatabase()
    
    def table(self, table_name: str):
        """Get table reference."""
        return self.db.table(table_name)


def get_mock_db():
    """Get or create mock database instance."""
    db_instance = MockDatabase()
    
    # Attach mock Supabase client
    class MockDBWrapper:
        def __init__(self, mock_db):
            self.mock_db = mock_db
            self.supabase = MockSupabaseClient()
    
    return MockDBWrapper(db_instance)
