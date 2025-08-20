#[cfg(test)]
mod tests {
    use super::super::*;
    use crate::data::types::{TickData, MarketDataType, DataLevel, OrderBookOperation};
    use rust_decimal::Decimal;
    use std::str::FromStr;

    fn create_test_tick(
        mdt: MarketDataType,
        price: &str,
        volume: i32,
        timestamp: i64,
    ) -> TickData {
        TickData::new(
            DataLevel::L1,
            mdt,
            timestamp,
            Decimal::from_str(price).unwrap(),
            volume,
            "0624".to_string(),
        )
    }

    fn create_l2_tick(
        mdt: MarketDataType,
        price: &str,
        volume: i32,
        timestamp: i64,
        operation: OrderBookOperation,
        depth: u8,
    ) -> TickData {
        TickData::new(
            DataLevel::L2,
            mdt,
            timestamp,
            Decimal::from_str(price).unwrap(),
            volume,
            "0624".to_string(),
        ).with_l2_data(operation, depth)
    }

    #[test]
    fn test_order_book_creation() {
        let book = OrderBook::new("MNQZ24".to_string());
        assert_eq!(book.symbol, "MNQZ24");
        assert_eq!(book.bid_levels.len(), 0);
        assert_eq!(book.ask_levels.len(), 0);
        assert_eq!(book.last_update_time, 0);
        assert!(book.best_bid.is_none());
        assert!(book.best_ask.is_none());
    }

    #[test]
    fn test_add_bid_level() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Add first bid
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        
        assert_eq!(book.bid_levels.len(), 1);
        assert_eq!(book.best_bid, Some(Decimal::from_str("4500.00").unwrap()));
        assert_eq!(book.last_update_time, 1000);
        
        // Add higher bid (new best)
        book.add_bid_level(Decimal::from_str("4500.25").unwrap(), 5, 2000);
        
        assert_eq!(book.bid_levels.len(), 2);
        assert_eq!(book.best_bid, Some(Decimal::from_str("4500.25").unwrap()));
        assert_eq!(book.last_update_time, 2000);
        
        // Add lower bid
        book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 15, 3000);
        
        assert_eq!(book.bid_levels.len(), 3);
        assert_eq!(book.best_bid, Some(Decimal::from_str("4500.25").unwrap())); // Unchanged
        assert_eq!(book.last_update_time, 3000);
    }

    #[test]
    fn test_add_ask_level() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Add first ask
        book.add_ask_level(Decimal::from_str("4501.00").unwrap(), 10, 1000);
        
        assert_eq!(book.ask_levels.len(), 1);
        assert_eq!(book.best_ask, Some(Decimal::from_str("4501.00").unwrap()));
        assert_eq!(book.last_update_time, 1000);
        
        // Add lower ask (new best)
        book.add_ask_level(Decimal::from_str("4500.75").unwrap(), 5, 2000);
        
        assert_eq!(book.ask_levels.len(), 2);
        assert_eq!(book.best_ask, Some(Decimal::from_str("4500.75").unwrap()));
        assert_eq!(book.last_update_time, 2000);
        
        // Add higher ask
        book.add_ask_level(Decimal::from_str("4501.25").unwrap(), 15, 3000);
        
        assert_eq!(book.ask_levels.len(), 3);
        assert_eq!(book.best_ask, Some(Decimal::from_str("4500.75").unwrap())); // Unchanged
        assert_eq!(book.last_update_time, 3000);
    }

    #[test]
    fn test_update_bid_level() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Add initial bid levels
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 15, 2000);
        
        // Update existing level
        book.update_bid_level(Decimal::from_str("4500.00").unwrap(), 20, 3000);
        
        let level = book.bid_levels.get(&Decimal::from_str("4500.00").unwrap()).unwrap();
        assert_eq!(level.quantity, 20);
        assert_eq!(level.last_update, 3000);
        
        // Update with zero quantity (should remove)
        book.update_bid_level(Decimal::from_str("4499.75").unwrap(), 0, 4000);
        
        assert_eq!(book.bid_levels.len(), 1);
        assert!(!book.bid_levels.contains_key(&Decimal::from_str("4499.75").unwrap()));
    }

    #[test]
    fn test_remove_bid_level() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Add bid levels
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 15, 2000);
        book.add_bid_level(Decimal::from_str("4499.50").unwrap(), 20, 3000);
        
        // Remove middle level
        book.remove_bid_level(Decimal::from_str("4499.75").unwrap(), 4000);
        
        assert_eq!(book.bid_levels.len(), 2);
        assert!(!book.bid_levels.contains_key(&Decimal::from_str("4499.75").unwrap()));
        assert_eq!(book.best_bid, Some(Decimal::from_str("4500.00").unwrap()));
        
        // Remove best bid
        book.remove_bid_level(Decimal::from_str("4500.00").unwrap(), 5000);
        
        assert_eq!(book.bid_levels.len(), 1);
        assert_eq!(book.best_bid, Some(Decimal::from_str("4499.50").unwrap()));
        
        // Remove last bid
        book.remove_bid_level(Decimal::from_str("4499.50").unwrap(), 6000);
        
        assert_eq!(book.bid_levels.len(), 0);
        assert!(book.best_bid.is_none());
    }

    #[test]
    fn test_get_spread() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // No spread when book is empty
        assert!(book.get_spread().is_none());
        
        // No spread with only bids
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        assert!(book.get_spread().is_none());
        
        // No spread with only asks
        let mut book = OrderBook::new("MNQZ24".to_string());
        book.add_ask_level(Decimal::from_str("4501.00").unwrap(), 10, 1000);
        assert!(book.get_spread().is_none());
        
        // Valid spread
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 2000);
        assert_eq!(book.get_spread(), Some(Decimal::from_str("1.00").unwrap()));
        
        // Tighter spread
        book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 5, 3000);
        assert_eq!(book.get_spread(), Some(Decimal::from_str("0.25").unwrap()));
    }

    #[test]
    fn test_get_mid_price() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // No mid price when book is empty
        assert!(book.get_mid_price().is_none());
        
        // No mid price with only one side
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        assert!(book.get_mid_price().is_none());
        
        // Valid mid price
        book.add_ask_level(Decimal::from_str("4501.00").unwrap(), 10, 2000);
        assert_eq!(book.get_mid_price(), Some(Decimal::from_str("4500.50").unwrap()));
        
        // Updated mid price
        book.add_ask_level(Decimal::from_str("4500.50").unwrap(), 5, 3000);
        assert_eq!(book.get_mid_price(), Some(Decimal::from_str("4500.25").unwrap()));
    }

    #[test]
    fn test_validate_integrity() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Empty book is valid
        assert!(book.validate_integrity());
        
        // Valid book with proper bid/ask relationship
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 10, 2000);
        assert!(book.validate_integrity());
        
        // Force invalid state (bid > ask) - should not happen in normal operation
        book.bid_levels.clear();
        book.add_bid_level(Decimal::from_str("4501.00").unwrap(), 10, 3000);
        book.best_bid = Some(Decimal::from_str("4501.00").unwrap());
        assert!(!book.validate_integrity()); // Should fail validation
    }

    #[test]
    fn test_process_mdt_0_trade() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        let mut reconstructor = OrderBookReconstructor::new();
        
        // Set up initial book state
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 10, 2000);
        
        // Process trade tick
        let trade = create_test_tick(
            MarketDataType::Trade,
            "4500.10",
            5,
            3000,
        );
        
        reconstructor.process_tick(&trade, &mut book).unwrap();
        
        assert_eq!(book.last_trade_price, Some(Decimal::from_str("4500.10").unwrap()));
        assert_eq!(book.last_trade_volume, Some(5));
        assert_eq!(book.last_trade_time, Some(3000));
    }

    #[test]
    fn test_process_mdt_1_bid_quote() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        let mut reconstructor = OrderBookReconstructor::new();
        
        // Process bid quote (best bid update)
        let bid = create_test_tick(
            MarketDataType::BidQuote,
            "4500.00",
            15,
            1000,
        );
        
        reconstructor.process_tick(&bid, &mut book).unwrap();
        
        assert_eq!(book.best_bid, Some(Decimal::from_str("4500.00").unwrap()));
        assert_eq!(book.bid_levels.len(), 1);
        
        let level = book.bid_levels.get(&Decimal::from_str("4500.00").unwrap()).unwrap();
        assert_eq!(level.quantity, 15);
    }

    #[test]
    fn test_process_mdt_2_ask_quote() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        let mut reconstructor = OrderBookReconstructor::new();
        
        // Process ask quote (best ask update)
        let ask = create_test_tick(
            MarketDataType::AskQuote,
            "4501.00",
            20,
            1000,
        );
        
        reconstructor.process_tick(&ask, &mut book).unwrap();
        
        assert_eq!(book.best_ask, Some(Decimal::from_str("4501.00").unwrap()));
        assert_eq!(book.ask_levels.len(), 1);
        
        let level = book.ask_levels.get(&Decimal::from_str("4501.00").unwrap()).unwrap();
        assert_eq!(level.quantity, 20);
    }

    #[test]
    fn test_process_l2_operations() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        let mut reconstructor = OrderBookReconstructor::new();
        
        // Add operation
        let add_tick = create_l2_tick(
            MarketDataType::BidQuote,
            "4500.00",
            10,
            1000,
            OrderBookOperation::Add,
            1,
        );
        reconstructor.process_tick(&add_tick, &mut book).unwrap();
        assert_eq!(book.bid_levels.len(), 1);
        
        // Update operation
        let update_tick = create_l2_tick(
            MarketDataType::BidQuote,
            "4500.00",
            20,
            2000,
            OrderBookOperation::Update,
            1,
        );
        reconstructor.process_tick(&update_tick, &mut book).unwrap();
        
        let level = book.bid_levels.get(&Decimal::from_str("4500.00").unwrap()).unwrap();
        assert_eq!(level.quantity, 20);
        
        // Remove operation
        let remove_tick = create_l2_tick(
            MarketDataType::BidQuote,
            "4500.00",
            0,
            3000,
            OrderBookOperation::Remove,
            1,
        );
        reconstructor.process_tick(&remove_tick, &mut book).unwrap();
        assert_eq!(book.bid_levels.len(), 0);
    }

    #[test]
    fn test_implied_quotes() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        let mut reconstructor = OrderBookReconstructor::new();
        
        // Process implied bid (MDT 3)
        let implied_bid = create_test_tick(
            MarketDataType::ImpliedBid,
            "4499.75",
            5,
            1000,
        );
        reconstructor.process_tick(&implied_bid, &mut book).unwrap();
        
        // Should be added as regular bid
        assert_eq!(book.bid_levels.len(), 1);
        assert!(book.bid_levels.contains_key(&Decimal::from_str("4499.75").unwrap()));
        
        // Process implied ask (MDT 4)
        let implied_ask = create_test_tick(
            MarketDataType::ImpliedAsk,
            "4501.25",
            5,
            2000,
        );
        reconstructor.process_tick(&implied_ask, &mut book).unwrap();
        
        // Should be added as regular ask
        assert_eq!(book.ask_levels.len(), 1);
        assert!(book.ask_levels.contains_key(&Decimal::from_str("4501.25").unwrap()));
    }

    #[test]
    fn test_book_reset() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Add some levels
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 15, 2000);
        book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 10, 3000);
        book.add_ask_level(Decimal::from_str("4500.50").unwrap(), 20, 4000);
        book.last_trade_price = Some(Decimal::from_str("4500.10").unwrap());
        
        // Reset the book
        book.reset();
        
        assert_eq!(book.bid_levels.len(), 0);
        assert_eq!(book.ask_levels.len(), 0);
        assert!(book.best_bid.is_none());
        assert!(book.best_ask.is_none());
        assert!(book.last_trade_price.is_none());
        assert!(book.last_trade_volume.is_none());
        assert!(book.last_trade_time.is_none());
        assert_eq!(book.last_update_time, 0);
    }

    #[test]
    fn test_get_book_depth() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Empty book
        assert_eq!(book.get_book_depth(), (0, 0));
        
        // Add bid levels
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 15, 2000);
        book.add_bid_level(Decimal::from_str("4499.50").unwrap(), 20, 3000);
        
        assert_eq!(book.get_book_depth(), (3, 0));
        
        // Add ask levels
        book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 10, 4000);
        book.add_ask_level(Decimal::from_str("4500.50").unwrap(), 15, 5000);
        
        assert_eq!(book.get_book_depth(), (3, 2));
    }

    #[test]
    fn test_get_total_bid_volume() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        assert_eq!(book.get_total_bid_volume(), 0);
        
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        assert_eq!(book.get_total_bid_volume(), 10);
        
        book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 15, 2000);
        assert_eq!(book.get_total_bid_volume(), 25);
        
        book.add_bid_level(Decimal::from_str("4499.50").unwrap(), 20, 3000);
        assert_eq!(book.get_total_bid_volume(), 45);
    }

    #[test]
    fn test_get_total_ask_volume() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        assert_eq!(book.get_total_ask_volume(), 0);
        
        book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 10, 1000);
        assert_eq!(book.get_total_ask_volume(), 10);
        
        book.add_ask_level(Decimal::from_str("4500.50").unwrap(), 15, 2000);
        assert_eq!(book.get_total_ask_volume(), 25);
        
        book.add_ask_level(Decimal::from_str("4500.75").unwrap(), 20, 3000);
        assert_eq!(book.get_total_ask_volume(), 45);
    }

    #[test]
    fn test_order_book_snapshot() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Build a book
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 10, 1000);
        book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 15, 2000);
        book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 5, 3000);
        book.add_ask_level(Decimal::from_str("4500.50").unwrap(), 20, 4000);
        book.last_trade_price = Some(Decimal::from_str("4500.10").unwrap());
        book.last_trade_volume = Some(3);
        
        // Create snapshot
        let snapshot = book.snapshot();
        
        assert_eq!(snapshot.symbol, "MNQZ24");
        assert_eq!(snapshot.best_bid, Some(Decimal::from_str("4500.00").unwrap()));
        assert_eq!(snapshot.best_ask, Some(Decimal::from_str("4500.25").unwrap()));
        assert_eq!(snapshot.spread, Some(Decimal::from_str("0.25").unwrap()));
        assert_eq!(snapshot.mid_price, Some(Decimal::from_str("4500.125").unwrap()));
        assert_eq!(snapshot.last_trade_price, Some(Decimal::from_str("4500.10").unwrap()));
        assert_eq!(snapshot.bid_depth, 2);
        assert_eq!(snapshot.ask_depth, 2);
        assert_eq!(snapshot.total_bid_volume, 25);
        assert_eq!(snapshot.total_ask_volume, 25);
    }

    #[test]
    fn test_chronological_processing() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        let mut reconstructor = OrderBookReconstructor::new();
        
        // Create ticks with mixed timestamps (simulating out-of-order data)
        let ticks = vec![
            create_test_tick(MarketDataType::BidQuote, "4500.00", 10, 1000),
            create_test_tick(MarketDataType::AskQuote, "4500.50", 10, 900), // Earlier timestamp
            create_test_tick(MarketDataType::Trade, "4500.25", 5, 1100),
        ];
        
        // Process all ticks
        for tick in &ticks {
            let _ = reconstructor.process_tick(tick, &mut book);
        }
        
        // Book should reflect the state after all ticks
        // The ask from timestamp 900 should have been processed
        assert_eq!(book.best_bid, Some(Decimal::from_str("4500.00").unwrap()));
        assert_eq!(book.best_ask, Some(Decimal::from_str("4500.50").unwrap()));
        assert_eq!(book.last_trade_price, Some(Decimal::from_str("4500.25").unwrap()));
        
        // Last update should be from the latest processed tick
        assert_eq!(book.last_update_time, 1100);
    }

    #[test]
    fn test_settlement_and_volume_ticks() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        let mut reconstructor = OrderBookReconstructor::new();
        
        // Process settlement tick (MDT 10)
        let settlement = create_test_tick(
            MarketDataType::Settlement,
            "4505.00",
            0,
            1000,
        );
        
        reconstructor.process_tick(&settlement, &mut book).unwrap();
        
        // Settlement should not affect the order book levels
        assert_eq!(book.bid_levels.len(), 0);
        assert_eq!(book.ask_levels.len(), 0);
        
        // Process volume tick (MDT 9)
        let volume = create_test_tick(
            MarketDataType::Volume,
            "0",
            12345,
            2000,
        );
        
        reconstructor.process_tick(&volume, &mut book).unwrap();
        
        // Volume should not affect the order book levels
        assert_eq!(book.bid_levels.len(), 0);
        assert_eq!(book.ask_levels.len(), 0);
    }

    #[test]
    fn test_book_imbalance_calculation() {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Equal volumes
        book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 20, 1000);
        book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 20, 2000);
        
        let bid_vol = book.get_total_bid_volume() as f64;
        let ask_vol = book.get_total_ask_volume() as f64;
        let imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol);
        
        assert_eq!(imbalance, 0.0); // Perfectly balanced
        
        // More bid volume
        book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 30, 3000);
        
        let bid_vol = book.get_total_bid_volume() as f64;
        let ask_vol = book.get_total_ask_volume() as f64;
        let imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol);
        
        assert!(imbalance > 0.0); // Positive imbalance (more bids)
        assert!((imbalance - 0.4285).abs() < 0.001); // 50 vs 20 = 0.4285...
        
        // More ask volume
        book.add_ask_level(Decimal::from_str("4500.50").unwrap(), 50, 4000);
        
        let bid_vol = book.get_total_bid_volume() as f64;
        let ask_vol = book.get_total_ask_volume() as f64;
        let imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol);
        
        assert!(imbalance < 0.0); // Negative imbalance (more asks)
    }
}