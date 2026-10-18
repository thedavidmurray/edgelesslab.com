"""
memory_helper.py - Memory system integration for Claude Code hooks
Provides unified interface to the centralized memory restoration system.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Memory system paths
MEMORY_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent)) / ".claude" / "memory"
SESSION_INIT_PATH = MEMORY_DIR / "session_initializer.py"
MEMORY_COORD_PATH = MEMORY_DIR / "memory_coordinator.py"
CONNECTORS_DIR = MEMORY_DIR / "connectors"
CONFIG_PATH = MEMORY_DIR / "configs" / "memory_sources.yaml"


class MemoryHelper:
    """Helper class for memory system integration."""

    def __init__(self):
        """Initialize memory helper."""
        self.initialized = False
        self.coordinator = None
        self.status = {}

    def check_availability(self) -> Dict[str, Any]:
        """Check if memory system components are available."""
        status = {
            "available": MEMORY_DIR.exists(),
            "session_initializer": SESSION_INIT_PATH.exists(),
            "memory_coordinator": MEMORY_COORD_PATH.exists(),
            "config": CONFIG_PATH.exists(),
            "connectors": []
        }

        if CONNECTORS_DIR.exists():
            status["connectors"] = [
                f.stem.replace("_connector", "")
                for f in CONNECTORS_DIR.glob("*_connector.py")
            ]

        self.status = status
        return status

    def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all memory systems."""
        health = {
            "overall": "unknown",
            "systems": {},
            "last_check": datetime.now().isoformat()
        }

        status = self.check_availability()

        for connector in status.get("connectors", []):
            health["systems"][connector] = self._check_connector_health(connector)

        # Determine overall health
        healths = list(health["systems"].values())
        if all(h.get("healthy") for h in healths):
            health["overall"] = "healthy"
        elif any(h.get("healthy") for h in healths):
            health["overall"] = "degraded"
        else:
            health["overall"] = "unhealthy"

        return health

    def _check_connector_health(self, connector_name: str) -> Dict[str, Any]:
        """Check health of a specific connector."""
        connector_path = CONNECTORS_DIR / f"{connector_name}_connector.py"

        health = {
            "exists": connector_path.exists(),
            "healthy": False,
            "error": None
        }

        if not health["exists"]:
            health["error"] = "Connector file not found"
            return health

        # Basic health check - file exists and is readable
        try:
            with open(connector_path, "r") as f:
                content = f.read()
                health["healthy"] = len(content) > 100  # Minimal validation
        except Exception as e:
            health["error"] = str(e)

        return health

    def query_memory(self, query: str, source: Optional[str] = None,
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query memory systems.

        Args:
            query: Search query
            source: Specific source to query (chromadb, pytorch, vault)
            limit: Maximum results to return

        Returns:
            List of memory results
        """
        results = []

        # Try to use memory coordinator if available
        if MEMORY_COORD_PATH.exists():
            try:
                sys.path.insert(0, str(MEMORY_DIR))
                from memory_coordinator import MemoryCoordinator

                coordinator = MemoryCoordinator()
                raw_results = coordinator.search(query, source=source, limit=limit)

                if raw_results:
                    results = self._normalize_results(raw_results)
            except Exception as e:
                results = [{"error": str(e), "source": "coordinator"}]
            finally:
                if str(MEMORY_DIR) in sys.path:
                    sys.path.remove(str(MEMORY_DIR))

        return results

    def _normalize_results(self, raw_results: Any) -> List[Dict[str, Any]]:
        """Normalize results from different sources to common format."""
        normalized = []

        if isinstance(raw_results, list):
            for item in raw_results:
                if isinstance(item, dict):
                    normalized.append({
                        "content": item.get("content", item.get("text", str(item))),
                        "source": item.get("source", "unknown"),
                        "metadata": item.get("metadata", {}),
                        "relevance": item.get("relevance", item.get("score", 0))
                    })
                else:
                    normalized.append({
                        "content": str(item),
                        "source": "unknown",
                        "metadata": {},
                        "relevance": 0
                    })

        return normalized

    def get_recent_context(self, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent context from memory systems."""
        # Query for recent activity
        return self.query_memory(
            f"recent activity last {days} days",
            limit=limit
        )

    def save_context(self, context: Dict[str, Any], context_type: str = "session") -> bool:
        """
        Save context to memory systems.

        Args:
            context: Context data to save
            context_type: Type of context (session, decision, learning, etc.)

        Returns:
            True if saved successfully
        """
        try:
            # Save to local log as fallback
            log_path = MEMORY_DIR / "logs" / f"{context_type}_log.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)

            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": context_type,
                "context": context
            }

            with open(log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")

            return True
        except Exception:
            return False


# Convenience functions for simple usage
def check_memory_available() -> bool:
    """Quick check if memory system is available."""
    helper = MemoryHelper()
    status = helper.check_availability()
    return status.get("available", False)


def get_memory_status() -> Dict[str, Any]:
    """Get memory system status."""
    helper = MemoryHelper()
    return helper.check_availability()


def query(query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Quick query interface."""
    helper = MemoryHelper()
    return helper.query_memory(query_text, limit=limit)
