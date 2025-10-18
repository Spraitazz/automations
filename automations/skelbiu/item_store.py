"""
Item Store Module

Encapsulates all logic related to storing and managing item renewal timestamps.

Provides an API for checking renewal needs and updating item states.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from automations.skelbiu.renewal_status import RenewalStatus


class ItemStore:
    """
    Manages item renewal state persistence.

    This item store is a dict with the unique item idx as keys and
    last updated datetime (iso format) as values, stored in json format.

    Stores items with their last renewal timestamps and provides logic
    to determine when items need to be checked/renewed.
    """

    # Threshold in seconds (25 hours)
    RENEWAL_THRESHOLD_SECONDS = 90000.0

    def __init__(self, store_filepath: Path, logger: logging.Logger):
        """
        Initialize the ItemStore.

        Args:
            store_filepath: Path to the JSON file storing item data
            logger: Optional logger instance for logging operations
        """
        self.store_filepath = store_filepath
        self.logger = logger
        self._items: Dict[str, str] = {}

    def load(self) -> None:
        """
        Load items from the store file.

        Creates the file if it doesn't exist.
        """
        try:
            with open(self.store_filepath, "r", encoding="utf-8") as f:
                self._items = json.load(f)
            self.logger.info(f"Loaded {len(self._items)} items from store")
        except FileNotFoundError:
            self.logger.warning(
                f"Item store file not found at {self.store_filepath}, creating"
            )
            self.store_filepath.touch()
            self._items = {}
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON in store file, resetting to empty")
            self._items = {}
        except Exception:
            self.logger.exception("Failed to load item store")
            self._items = {}

    def save(self) -> None:
        """
        Save current items to the store file.
        """
        try:
            with open(self.store_filepath, "w", encoding="utf-8") as f:
                json.dump(self._items, f, indent=2)
            self.logger.debug(f"Saved {len(self._items)} items to store")
        except Exception:
            self.logger.exception("Failed to save item store")

    def get_items(self) -> Dict[str, str]:
        """
        Get a copy of all stored items.

        Returns:
            Dictionary mapping item_id -> last_renewed_timestamp (ISO format)
        """
        return self._items.copy()

    def check_needs_renewal(self) -> bool:
        """
        Check if any items need renewal based on stored state.

        Returns True if:
        1. No items in store (first run)
        2. Any item has unknown last updated date (empty or "-")
        3. Any item was last updated more than RENEWAL_THRESHOLD_SECONDS ago

        Returns:
            True if renewal check is needed, False otherwise
        """
        if len(self._items) == 0:
            self.logger.debug("No items in store, renewal check needed")
            return True

        now = datetime.now()

        for item_id, last_updated_str in self._items.items():
            # Check for unknown/empty timestamp
            if not last_updated_str or len(last_updated_str) < 2:
                self.logger.debug(
                    f"Item {item_id} has unknown last update time, renewal check needed"
                )
                return True

            # Check if past threshold
            try:
                datetime_last_updated = datetime.fromisoformat(last_updated_str)
                time_since_update = (now - datetime_last_updated).total_seconds()

                if time_since_update > self.RENEWAL_THRESHOLD_SECONDS:
                    hours_since = time_since_update / 3600
                    self.logger.debug(
                        f"Item {item_id} last updated {hours_since:.1f}h ago, "
                        f"renewal check needed"
                    )
                    return True
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    f"Invalid timestamp for item {item_id}: "
                    f"{last_updated_str}, "
                    f"renewal check needed. Error: {e}"
                )
                return True

        self.logger.debug("All items are up to date, no renewal check needed")
        return False

    def update_from_renewal_result(self, renewal_result: Dict[str, dict]) -> None:
        """
        Update stored items based on renewal operation results.

        Args:
            renewal_result: Dictionary mapping item_id to status dict with keys:
                           - 'status': RenewalStatus enum value
                           - 'last_renewed': ISO format timestamp (if status
                           is RENEWED)

        The method:
        - Updates timestamp for newly renewed items
        - Preserves existing timestamps for already-renewed items
        - Sets unknown timestamp ("-") for items without history
        - Logs failed renewals but doesn't update their timestamps
        """
        updated_items = {}

        for item_id, status_dict in renewal_result.items():
            status = status_dict["status"]

            if status == RenewalStatus.RENEWED:
                # Item was just renewed, use new timestamp
                updated_items[item_id] = status_dict["last_renewed"]
                self.logger.debug(
                    f"Updated item {item_id} with new renewal time: "
                    f"{status_dict['last_renewed']}"
                )
            elif status == RenewalStatus.ALREADY_RENEWED:
                # Item was already renewed, preserve existing timestamp if available
                if item_id in self._items:
                    updated_items[item_id] = self._items[item_id]
                    self.logger.debug(
                        f"Item {item_id} already renewed, preserving timestamp"
                    )
                else:
                    # New item with unknown timestamp
                    updated_items[item_id] = "-"
                    self.logger.debug(f"Item {item_id} is new with unknown timestamp")
            elif status == RenewalStatus.FAILED:
                # Item renewal failed, preserve existing timestamp if available
                if item_id in self._items:
                    updated_items[item_id] = self._items[item_id]
                    self.logger.warning(
                        f"Item {item_id} renewal failed, preserving old timestamp"
                    )
                else:
                    updated_items[item_id] = "-"
                    self.logger.warning(
                        f"Item {item_id} renewal failed, marking with unknown timestamp"
                    )

        self._items = updated_items
        self.save()
        self.logger.info(f"Item store updated with {len(self._items)} items")

    def get_item_count(self) -> int:
        """
        Get the number of items in the store.

        Returns:
            Number of stored items
        """
        return len(self._items)

    def clear(self) -> None:
        """
        Clear all items from the store and save.
        """
        self._items = {}
        self.save()
        self.logger.info("Item store cleared")
