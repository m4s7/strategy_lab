"""Parquet file discovery system for MNQ tick data."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParquetFileInfo:
    """Information about a single Parquet file."""

    path: Path
    contract_month: str
    date: datetime
    size_bytes: int
    file_name: str

    @property
    def size_mb(self) -> float:
        """File size in megabytes."""
        return self.size_bytes / (1024 * 1024)


class ParquetFileDiscovery:
    """Discovers and indexes Parquet files in the MNQ data directory."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize the file discovery system.

        Args:
            data_dir: Path to the MNQ data directory. Defaults to ./data/MNQ
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/MNQ")
        self.cache_file = self.data_dir.parent / "MNQ_parquet_files.json"
        self.file_index_path = self.cache_file
        self._file_index: dict | None = None

    def discover_files(
        self,
        contract_months: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ParquetFileInfo]:
        """Discover Parquet files matching the given criteria.

        Args:
            contract_months: List of contract months to include (e.g., ["03-20", "06-20"])
            start_date: Include files from this date onwards
            end_date: Include files up to this date

        Returns:
            List of ParquetFileInfo objects for matching files
        """
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

        files = []

        # Get contract directories
        contract_dirs = self._get_contract_directories(contract_months)

        for contract_dir in contract_dirs:
            contract_month = contract_dir.name
            parquet_files = sorted(contract_dir.glob("*.parquet"))

            for file_path in parquet_files:
                try:
                    # Parse date from filename
                    file_date = self._parse_date_from_filename(file_path.name)

                    # Apply date filters
                    if start_date and file_date < start_date:
                        continue
                    if end_date and file_date > end_date:
                        continue

                    file_info = ParquetFileInfo(
                        path=file_path,
                        contract_month=contract_month,
                        date=file_date,
                        size_bytes=file_path.stat().st_size,
                        file_name=file_path.name,
                    )
                    files.append(file_info)

                except (ValueError, OSError) as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue

        logger.info(f"Discovered {len(files)} Parquet files")
        return sorted(files, key=lambda f: (f.contract_month, f.date))

    def _get_contract_directories(
        self, contract_months: list[str] | None = None
    ) -> list[Path]:
        """Get contract month directories to scan.

        Args:
            contract_months: Specific contract months to include, or None for all

        Returns:
            List of Path objects for contract directories
        """
        all_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]

        if not contract_months:
            return all_dirs

        # Filter to requested contract months
        contract_set = set(contract_months)
        return [d for d in all_dirs if d.name in contract_set]

    def load_file_index(self) -> dict:
        """Load the pre-built file index from JSON.

        Returns:
            Dictionary containing file metadata

        Raises:
            FileNotFoundError: If index file doesn't exist
        """
        if self._file_index is not None:
            return self._file_index

        if not self.file_index_path.exists():
            raise FileNotFoundError(
                f"File index not found: {self.file_index_path}. "
                "Please run generate_file_index() first."
            )

        with open(self.file_index_path) as f:
            self._file_index = json.load(f)

        logger.info(f"Loaded file index with {len(self._file_index)} entries")
        return self._file_index

    def generate_file_index(self) -> dict:
        """Generate a complete file index and save to JSON.

        Returns:
            Dictionary containing file metadata
        """
        logger.info("Generating file index...")
        files = self.discover_files()

        index = {}
        for file_info in files:
            key = f"{file_info.contract_month}/{file_info.file_name}"
            index[key] = {
                "path": str(file_info.path),
                "contract_month": file_info.contract_month,
                "date": file_info.date.isoformat(),
                "size_bytes": file_info.size_bytes,
                "size_mb": file_info.size_mb,
            }

        # Save to JSON
        with open(self.file_index_path, "w") as f:
            json.dump(index, f, indent=2)

        self._file_index = index
        logger.info(f"Generated index with {len(index)} files")
        return index

    def get_contract_months(self) -> list[str]:
        """Get list of available contract months.

        Returns:
            Sorted list of contract month strings (e.g., ["03-20", "06-20"])
        """
        if not self.data_dir.exists():
            return []

        contract_months = [
            d.name for d in self.data_dir.iterdir() if d.is_dir() and "-" in d.name
        ]
        return sorted(contract_months)

    def get_date_range(
        self, contract_month: str | None = None
    ) -> tuple[datetime, datetime]:
        """Get the date range of available data.

        Args:
            contract_month: Specific contract month, or None for all data

        Returns:
            Tuple of (earliest_date, latest_date)
        """
        files = self.discover_files(
            contract_months=[contract_month] if contract_month else None
        )

        if not files:
            raise ValueError("No files found")

        dates = [f.date for f in files]
        return min(dates), max(dates)

    def get_file_stats(self) -> dict:
        """Get statistics about the discovered files.

        Returns:
            Dictionary with file statistics
        """
        files = self.discover_files()

        if not files:
            return {
                "total_files": 0,
                "total_size_gb": 0,
                "contract_months": 0,
                "date_range": None,
            }

        total_size = sum(f.size_bytes for f in files)
        contract_months = set(f.contract_month for f in files)
        dates = [f.date for f in files]

        return {
            "total_files": len(files),
            "total_size_gb": total_size / (1024**3),
            "contract_months": len(contract_months),
            "date_range": (min(dates), max(dates)),
            "avg_file_size_mb": (total_size / len(files)) / (1024**2),
            "contracts": sorted(contract_months),
        }

    def _parse_date_from_filename(self, filename: str) -> datetime:
        """Parse date from various filename formats."""
        import re

        # Try format: MNQ_XX-XX_YYYY-MM-DD.parquet
        match = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
        if match:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day))

        # Try format: YYYYMMDD.parquet
        stem = Path(filename).stem
        if len(stem) == 8 and stem.isdigit():
            return datetime.strptime(stem, "%Y%m%d")

        raise ValueError(f"Cannot parse date from filename: {filename}")

    def _parse_filename(self, filename: str) -> dict[str, Any] | None:
        """Parse contract month and date from filename."""
        try:
            import re

            # Match pattern: MNQ_XX-XX_YYYY-MM-DD.parquet
            match = re.match(r"MNQ_(\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.parquet", filename)
            if match:
                contract_month = match.group(1)
                date_str = match.group(2)
                date = datetime.strptime(date_str, "%Y-%m-%d")
                return {
                    "contract_month": contract_month,
                    "date": date
                }
            return None
        except Exception:
            return None

    def save_cache(self, files: list[ParquetFileInfo]) -> None:
        """Save file information to cache."""
        cache_data = []
        for file_info in files:
            cache_data.append({
                "path": str(file_info.path),
                "contract_month": file_info.contract_month,
                "date": file_info.date.isoformat(),
                "size_mb": file_info.size_mb,
                "row_count": getattr(file_info, "row_count", None)
            })

        with open(self.cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

    def load_cache(self) -> list[ParquetFileInfo]:
        """Load file information from cache."""
        if not self.cache_file.exists():
            return []

        with open(self.cache_file) as f:
            cache_data = json.load(f)

        files = []
        for item in cache_data:
            # Handle the fact that ParquetFileInfo uses size_bytes not size_mb
            size_bytes = int(item.get("size_mb", 0) * 1024 * 1024) if "size_mb" in item else 0

            file_info = ParquetFileInfo(
                path=Path(item["path"]),
                contract_month=item["contract_month"],
                date=datetime.fromisoformat(item["date"]),
                size_bytes=size_bytes,
                file_name=Path(item["path"]).name
            )
            # Add row_count as an attribute if present
            if "row_count" in item and item["row_count"] is not None:
                setattr(file_info, "row_count", item["row_count"])
            files.append(file_info)

        return files
