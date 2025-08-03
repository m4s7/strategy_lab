"""Order book reconstruction engine for Level 2 market data."""

import bisect
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class OrderBookLevel:
    """Represents a single price level in the order book."""

    price: Decimal
    volume: int
    order_count: int = 0
    market_maker: str | None = None

    def __post_init__(self) -> None:
        """Ensure price is Decimal for precision."""
        # Convert to Decimal if not already
        self.price = Decimal(str(self.price))


@dataclass
class OrderBookSnapshot:
    """Snapshot of order book state at a specific timestamp."""

    timestamp: int
    bid_levels: list[OrderBookLevel] = field(default_factory=list)
    ask_levels: list[OrderBookLevel] = field(default_factory=list)

    @property
    def best_bid(self) -> OrderBookLevel | None:
        """Get the best bid price level."""
        return self.bid_levels[0] if self.bid_levels else None

    @property
    def best_ask(self) -> OrderBookLevel | None:
        """Get the best ask price level."""
        return self.ask_levels[0] if self.ask_levels else None

    @property
    def spread(self) -> Decimal | None:
        """Calculate bid-ask spread."""
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return None

    @property
    def mid_price(self) -> Decimal | None:
        """Calculate mid price."""
        if self.best_bid and self.best_ask:
            return (self.best_bid.price + self.best_ask.price) / 2
        return None


class OrderBookAnalytics:
    """Analytics calculator for order book metrics."""

    @staticmethod
    def calculate_imbalance(bid_volume: int, ask_volume: int) -> float:
        """
        Calculate order book imbalance.

        Formula: (Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)
        Returns value between -1 (all ask) and 1 (all bid).
        """
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return 0.0
        return (bid_volume - ask_volume) / total_volume

    @staticmethod
    def calculate_depth_weighted_price(
        levels: list[OrderBookLevel], depth: int = 5
    ) -> Decimal | None:
        """Calculate volume-weighted average price for given depth."""
        if not levels or depth <= 0:
            return None

        total_volume = 0
        weighted_price_sum = Decimal("0")

        for level in levels[:depth]:
            if level.volume > 0:
                total_volume += level.volume
                weighted_price_sum += level.price * level.volume

        if total_volume == 0:
            return None

        return weighted_price_sum / total_volume

    @staticmethod
    def calculate_book_pressure(
        snapshot: OrderBookSnapshot, depth: int = 5
    ) -> dict[str, float]:
        """Calculate various book pressure metrics."""
        bid_volume = sum(level.volume for level in snapshot.bid_levels[:depth])
        ask_volume = sum(level.volume for level in snapshot.ask_levels[:depth])

        return {
            "imbalance": OrderBookAnalytics.calculate_imbalance(bid_volume, ask_volume),
            "bid_volume": bid_volume,
            "ask_volume": ask_volume,
            "total_volume": bid_volume + ask_volume,
            "bid_ratio": (
                bid_volume / (bid_volume + ask_volume)
                if (bid_volume + ask_volume) > 0
                else 0.5
            ),
        }


class OrderBook:
    """
    Order book reconstruction engine for Level 2 market data.

    Maintains real-time order book state from Level 2 operations and provides
    analytics for market microstructure analysis.
    """

    # Operation types from MNQ schema
    OP_ADD = 0
    OP_UPDATE = 1
    OP_REMOVE = 2

    # Market data types
    MDT_ASK = 0
    MDT_BID = 1

    def __init__(self, max_depth: int = 10):
        """
        Initialize order book.

        Args:
            max_depth: Maximum depth levels to maintain
        """
        self.max_depth = max_depth
        self.reset()

    def reset(self) -> None:
        """Reset order book to empty state."""
        # Use sorted dictionaries to maintain price ordering
        # Bids: descending order (highest price first)
        # Asks: ascending order (lowest price first)
        self._bid_levels: dict[Decimal, OrderBookLevel] = {}
        self._ask_levels: dict[Decimal, OrderBookLevel] = {}

        # Maintain sorted price lists for efficient access
        self._bid_prices: list[Decimal] = []  # Sorted descending
        self._ask_prices: list[Decimal] = []  # Sorted ascending

        # Track last update timestamp
        self._last_timestamp: int | None = None

        # Performance counters
        self._operation_count = 0
        self._invalid_operations = 0

        logger.debug("Order book reset to empty state")

    def process_operation(
        self,
        timestamp: int,
        mdt: int,
        price: float,
        volume: int,
        operation: int,
        depth: int | None = None,  # noqa: ARG002
        market_maker: str | None = None,
    ) -> bool:
        """
        Process a single Level 2 operation.

        Args:
            timestamp: Operation timestamp in nanoseconds
            mdt: Market data type (0=Ask, 1=Bid)
            price: Price level
            volume: Volume at price level
            operation: Operation type (0=Add, 1=Update, 2=Remove)
            depth: Depth level (optional)
            market_maker: Market maker identifier (optional)

        Returns:
            True if operation was processed successfully
        """
        try:
            self._operation_count += 1

            # Validate timestamp ordering
            if self._last_timestamp and timestamp < self._last_timestamp:
                logger.warning(
                    f"Out-of-sequence timestamp: {timestamp} < {self._last_timestamp}"
                )
            self._last_timestamp = timestamp

            # Convert price to Decimal for precision
            price_decimal = Decimal(str(price))

            # Validate inputs
            if not self._validate_operation(mdt, price_decimal, volume, operation):
                self._invalid_operations += 1
                return False

            # Route to appropriate side
            if mdt == self.MDT_BID:
                return self._process_bid_operation(
                    price_decimal, volume, operation, market_maker
                )
            if mdt == self.MDT_ASK:
                return self._process_ask_operation(
                    price_decimal, volume, operation, market_maker
                )
            logger.warning(f"Unknown MDT: {mdt}")
            self._invalid_operations += 1
            return False

        except Exception as e:
            logger.exception(f"Error processing operation: {e}")
            self._invalid_operations += 1
            return False

    def _validate_operation(
        self, mdt: int, price: Decimal, volume: int, operation: int
    ) -> bool:
        """Validate operation parameters."""
        if mdt not in [self.MDT_ASK, self.MDT_BID]:
            logger.warning(f"Invalid MDT: {mdt}")
            return False

        if price <= 0:
            logger.warning(f"Invalid price: {price}")
            return False

        if operation not in [self.OP_ADD, self.OP_UPDATE, self.OP_REMOVE]:
            logger.warning(f"Invalid operation: {operation}")
            return False

        if operation != self.OP_REMOVE and volume < 0:
            logger.warning(f"Invalid volume for operation {operation}: {volume}")
            return False

        return True

    def _process_bid_operation(
        self,
        price: Decimal,
        volume: int,
        operation: int,
        market_maker: str | None = None,
    ) -> bool:
        """Process operation on bid side."""
        if operation == self.OP_ADD:
            return self._add_bid_level(price, volume, market_maker)
        if operation == self.OP_UPDATE:
            return self._update_bid_level(price, volume, market_maker)
        if operation == self.OP_REMOVE:
            return self._remove_bid_level(price)
        return False

    def _process_ask_operation(
        self,
        price: Decimal,
        volume: int,
        operation: int,
        market_maker: str | None = None,
    ) -> bool:
        """Process operation on ask side."""
        if operation == self.OP_ADD:
            return self._add_ask_level(price, volume, market_maker)
        if operation == self.OP_UPDATE:
            return self._update_ask_level(price, volume, market_maker)
        if operation == self.OP_REMOVE:
            return self._remove_ask_level(price)
        return False

    def _add_bid_level(
        self, price: Decimal, volume: int, market_maker: str | None = None
    ) -> bool:
        """Add new bid level."""
        if price in self._bid_levels:
            logger.warning(
                f"Bid level already exists at price {price}, updating instead"
            )
            return self._update_bid_level(price, volume, market_maker)

        level = OrderBookLevel(
            price=price, volume=volume, order_count=1, market_maker=market_maker
        )
        self._bid_levels[price] = level

        # Insert into sorted price list maintaining descending order
        # Use negative price for bisect to get descending order
        neg_price = -price
        insert_pos = bisect.bisect_left([-p for p in self._bid_prices], neg_price)
        self._bid_prices.insert(insert_pos, price)

        # Limit depth
        self._trim_bid_depth()

        return True

    def _add_ask_level(
        self, price: Decimal, volume: int, market_maker: str | None = None
    ) -> bool:
        """Add new ask level."""
        if price in self._ask_levels:
            logger.warning(
                f"Ask level already exists at price {price}, updating instead"
            )
            return self._update_ask_level(price, volume, market_maker)

        level = OrderBookLevel(
            price=price, volume=volume, order_count=1, market_maker=market_maker
        )
        self._ask_levels[price] = level

        # Insert into sorted price list (ascending order)
        bisect.insort_left(self._ask_prices, price)

        # Limit depth
        self._trim_ask_depth()

        return True

    def _update_bid_level(
        self, price: Decimal, volume: int, market_maker: str | None = None
    ) -> bool:
        """Update existing bid level."""
        if price not in self._bid_levels:
            logger.warning(f"No bid level exists at price {price}, adding instead")
            return self._add_bid_level(price, volume, market_maker)

        level = self._bid_levels[price]
        level.volume = volume
        if market_maker:
            level.market_maker = market_maker

        # Remove level if volume becomes zero
        if volume == 0:
            return self._remove_bid_level(price)

        return True

    def _update_ask_level(
        self, price: Decimal, volume: int, market_maker: str | None = None
    ) -> bool:
        """Update existing ask level."""
        if price not in self._ask_levels:
            logger.warning(f"No ask level exists at price {price}, adding instead")
            return self._add_ask_level(price, volume, market_maker)

        level = self._ask_levels[price]
        level.volume = volume
        if market_maker:
            level.market_maker = market_maker

        # Remove level if volume becomes zero
        if volume == 0:
            return self._remove_ask_level(price)

        return True

    def _remove_bid_level(self, price: Decimal) -> bool:
        """Remove bid level."""
        if price not in self._bid_levels:
            logger.warning(f"No bid level exists at price {price}")
            return False

        del self._bid_levels[price]
        self._bid_prices.remove(price)

        return True

    def _remove_ask_level(self, price: Decimal) -> bool:
        """Remove ask level."""
        if price not in self._ask_levels:
            logger.warning(f"No ask level exists at price {price}")
            return False

        del self._ask_levels[price]
        self._ask_prices.remove(price)

        return True

    def _trim_bid_depth(self) -> None:
        """Trim bid side to max depth."""
        while len(self._bid_prices) > self.max_depth:
            # Remove worst (lowest) bid price
            worst_price = self._bid_prices.pop()
            del self._bid_levels[worst_price]

    def _trim_ask_depth(self) -> None:
        """Trim ask side to max depth."""
        while len(self._ask_prices) > self.max_depth:
            # Remove worst (highest) ask price
            worst_price = self._ask_prices.pop()
            del self._ask_levels[worst_price]

    def get_snapshot(self, timestamp: int | None = None) -> OrderBookSnapshot:
        """
        Get current order book snapshot.

        Args:
            timestamp: Timestamp for snapshot (uses last update if None)

        Returns:
            OrderBookSnapshot with current state
        """
        snapshot_timestamp = timestamp or self._last_timestamp or 0

        # Build ordered level lists
        bid_levels = [self._bid_levels[price] for price in self._bid_prices]
        ask_levels = [self._ask_levels[price] for price in self._ask_prices]

        return OrderBookSnapshot(
            timestamp=snapshot_timestamp,
            bid_levels=bid_levels.copy(),
            ask_levels=ask_levels.copy(),
        )

    def get_best_bid(self) -> OrderBookLevel | None:
        """Get best bid level."""
        return self._bid_levels[self._bid_prices[0]] if self._bid_prices else None

    def get_best_ask(self) -> OrderBookLevel | None:
        """Get best ask level."""
        return self._ask_levels[self._ask_prices[0]] if self._ask_prices else None

    def get_spread(self) -> Decimal | None:
        """Get current bid-ask spread."""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid and best_ask:
            return best_ask.price - best_bid.price
        return None

    def get_mid_price(self) -> Decimal | None:
        """Get current mid price."""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid and best_ask:
            return (best_bid.price + best_ask.price) / 2
        return None

    def get_analytics(self, depth: int = 5) -> dict[str, Any]:
        """
        Get comprehensive order book analytics.

        Args:
            depth: Depth levels to include in analytics

        Returns:
            Dictionary with analytics metrics
        """
        snapshot = self.get_snapshot()

        # Basic metrics
        analytics = {
            "timestamp": self._last_timestamp,
            "best_bid": snapshot.best_bid.price if snapshot.best_bid else None,
            "best_ask": snapshot.best_ask.price if snapshot.best_ask else None,
            "spread": snapshot.spread,
            "mid_price": snapshot.mid_price,
            "bid_levels": len(self._bid_prices),
            "ask_levels": len(self._ask_prices),
        }

        # Pressure metrics
        pressure_metrics = OrderBookAnalytics.calculate_book_pressure(snapshot, depth)
        analytics.update(pressure_metrics)  # type: ignore[arg-type]

        # Depth-weighted prices
        analytics["bid_vwap"] = OrderBookAnalytics.calculate_depth_weighted_price(
            snapshot.bid_levels, depth
        )
        analytics["ask_vwap"] = OrderBookAnalytics.calculate_depth_weighted_price(
            snapshot.ask_levels, depth
        )

        # Performance metrics
        analytics["operation_count"] = self._operation_count
        analytics["invalid_operations"] = self._invalid_operations
        analytics["error_rate"] = float(self._invalid_operations) / max(1, self._operation_count)  # type: ignore[assignment]

        return analytics

    def process_dataframe(self, df: pd.DataFrame) -> int:
        """
        Process a DataFrame of Level 2 operations in bulk.

        Args:
            df: DataFrame with columns: timestamp, mdt, price, volume, operation

        Returns:
            Number of operations processed successfully
        """
        if df.empty:
            return 0

        # Ensure DataFrame is sorted by timestamp
        df = df.sort_values("timestamp")

        processed_count = 0

        for _, row in df.iterrows():
            success = self.process_operation(
                timestamp=int(row["timestamp"]),
                mdt=int(row["mdt"]),
                price=float(row["price"]),
                volume=int(row["volume"]),
                operation=int(row["operation"]),
                depth=row.get("depth"),
                market_maker=row.get("market_maker"),
            )

            if success:
                processed_count += 1

        logger.info(f"Processed {processed_count}/{len(df)} operations from DataFrame")
        return processed_count

    def is_valid_book(self) -> bool:
        """
        Check if current book state is valid.

        Returns:
            True if book is in valid state
        """
        # Check bid/ask crossing
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid and best_ask and best_bid.price >= best_ask.price:
            logger.error(f"Book crossed: bid {best_bid.price} >= ask {best_ask.price}")
            return False

        # Check price ordering on bid side (descending)
        for i in range(len(self._bid_prices) - 1):
            if self._bid_prices[i] < self._bid_prices[i + 1]:
                logger.error("Bid prices not in descending order")
                return False

        # Check price ordering on ask side (ascending)
        for i in range(len(self._ask_prices) - 1):
            if self._ask_prices[i] > self._ask_prices[i + 1]:
                logger.error("Ask prices not in ascending order")
                return False

        # Check that all levels have positive volume
        for level in self._bid_levels.values():
            if level.volume <= 0:
                logger.error(f"Bid level with non-positive volume: {level}")
                return False

        for level in self._ask_levels.values():
            if level.volume <= 0:
                logger.error(f"Ask level with non-positive volume: {level}")
                return False

        return True

    def __repr__(self) -> str:
        """String representation of order book."""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        return (
            f"OrderBook(bids={len(self._bid_prices)}, "
            f"asks={len(self._ask_prices)}, "
            f"best_bid={best_bid.price if best_bid else None}, "
            f"best_ask={best_ask.price if best_ask else None})"
        )


class OrderBookReconstructor:
    """
    High-level interface for reconstructing order books from historical data.
    """

    def __init__(self, max_depth: int = 10):
        """
        Initialize reconstructor.

        Args:
            max_depth: Maximum book depth to maintain
        """
        self.max_depth = max_depth
        self.order_book = OrderBook(max_depth)

    def reconstruct_from_file(
        self, file_path: str, timestamp: int | None = None
    ) -> OrderBookSnapshot:
        """
        Reconstruct order book from Level 2 data file.

        Args:
            file_path: Path to Parquet file with Level 2 data
            timestamp: Target timestamp (reconstructs full history if None)

        Returns:
            OrderBookSnapshot at target timestamp
        """
        # Load Level 2 data
        data_df = pd.read_parquet(file_path)

        # Filter Level 2 data only
        level2_data = data_df[data_df["level"] == "2"].copy()

        if timestamp:
            # Only process data up to target timestamp
            level2_data = level2_data[level2_data["timestamp"] <= timestamp]

        # Reset book and process operations
        self.order_book.reset()
        self.order_book.process_dataframe(level2_data)

        return self.order_book.get_snapshot(timestamp)

    def reconstruct_time_series(
        self,
        file_path: str,
        start_time: int,
        end_time: int,
        interval_ns: int = 1_000_000_000,  # 1 second default
    ) -> list[OrderBookSnapshot]:
        """
        Reconstruct order book snapshots over time range.

        Args:
            file_path: Path to Parquet file with Level 2 data
            start_time: Start timestamp in nanoseconds
            end_time: End timestamp in nanoseconds
            interval_ns: Snapshot interval in nanoseconds

        Returns:
            List of OrderBookSnapshots at regular intervals
        """
        # Load and filter data
        data_df = pd.read_parquet(file_path)
        level2_data = (
            data_df[
                (data_df["level"] == "2")
                & (data_df["timestamp"] >= start_time)
                & (data_df["timestamp"] <= end_time)
            ]
            .copy()
            .sort_values("timestamp")
        )

        snapshots = []
        current_time = start_time
        data_index = 0

        # Reset book
        self.order_book.reset()

        while current_time <= end_time:
            # Process all operations up to current_time
            while (
                data_index < len(level2_data)
                and level2_data.iloc[data_index]["timestamp"] <= current_time
            ):
                row = level2_data.iloc[data_index]
                self.order_book.process_operation(
                    timestamp=int(row["timestamp"]),
                    mdt=int(row["mdt"]),
                    price=float(row["price"]),
                    volume=int(row["volume"]),
                    operation=int(row["operation"]),
                    depth=row.get("depth"),
                    market_maker=row.get("market_maker"),
                )
                data_index += 1

            # Take snapshot
            snapshot = self.order_book.get_snapshot(current_time)
            snapshots.append(snapshot)

            current_time += interval_ns

        return snapshots
