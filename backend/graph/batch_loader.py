"""
MedGraph AI — Reusable Batched Execution Utilities
=================================================
Executes parameterized Cypher queries in transaction-safe batches.

Handles data chunking, NaN sanitization, and explicit transaction management.
"""

import logging
import math
from typing import List, Dict, Any, Generator

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 5000

def sanitize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a data dictionary for Neo4j Cypher compatibility.
    Replaces Python NaN / float('nan') values with None (which maps to Cypher null).
    """
    clean = {}
    for key, val in record.items():
        if isinstance(val, float) and math.isnan(val):
            clean[key] = None
        else:
            clean[key] = val
    return clean

def chunk_list(data: List[Dict[str, Any]], chunk_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """Yield successive chunks of size chunk_size from data."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def execute_batch_write(
    session,
    cypher_query: str,
    records: List[Dict[str, Any]],
    batch_name: str = "batch",
    batch_size: int = DEFAULT_BATCH_SIZE
) -> int:
    """
    Execute a parameterized Cypher query over a list of records in transaction batches.

    Args:
        session: Active Neo4j session instance.
        cypher_query: Parameterized Cypher query with $batch placeholder.
        records: List of dictionaries representing rows to load.
        batch_name: Human-readable label for logging.
        batch_size: Number of records per transaction (default: 5000).

    Returns:
        int: Total number of records successfully written.
    """
    if not records:
        logger.warning("No records provided for batch write '%s'. Skipping.", batch_name)
        return 0

    total_records = len(records)
    logger.info("Starting batched write for '%s' (%d total records, batch_size=%d)", 
                batch_name, total_records, batch_size)

    # Sanitize all records to eliminate float NaNs
    sanitized_records = [sanitize_record(r) for r in records]

    written_count = 0
    chunk_index = 0

    for batch_chunk in chunk_list(sanitized_records, batch_size):
        chunk_index += 1
        
        def _tx_write(tx):
            tx.run(cypher_query, batch=batch_chunk)

        session.execute_write(_tx_write)
        written_count += len(batch_chunk)
        logger.debug("  ✓ [%s] Batch %d written (%d/%d records)", 
                     batch_name, chunk_index, written_count, total_records)

    logger.info("Finished batched write for '%s' (Total: %d records)", batch_name, written_count)
    return written_count
