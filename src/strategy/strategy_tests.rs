#[cfg(test)]
mod tests {
    use super::super::traits::*;
    use super::super::{Order, OrderType, OrderSide, StrategyConfig, Position};
use super::super::traits::OrderFill;
    use crate::data::TickData;
    use crate::market::OrderBookState;
    use rust_decimal::Decimal;
    use std::str::FromStr;
    use chrono::Utc;

    // Mock strategy for testing
    #[derive(Clone)]
    struct MockStrategy {
        config: StrategyConfig,
        position: Position,
        order_count: usize,
        should_generate_order: bool,
    }

    impl MockStrategy {
        fn new() -> Self {
            Self {
                config: StrategyConfig::default(),
                position: Position::Flat,
                order_count: 0,
                should_generate_order: true,
            }
        }
    }

    impl Strategy for MockStrategy {
        fn on_tick(&mut self, tick: &TickData, context: &StrategyContext) -> Option<Order> {
            if !self.should_generate_order {
                return None;
            }

            self.order_count += 1;

            // Generate alternating buy/sell orders
            if self.order_count % 2 == 1 {
                Some(Order {
                    symbol: "MNQZ24".to_string(),
                    side: OrderSide::Buy,
                    quantity: 1,
                    order_type: OrderType::Market,
                    price: Some(tick.price),
                    timestamp: Utc::now(),
                    id: format!("ORDER_{}", self.order_count),
                })
            } else {
                Some(Order {
                    symbol: "MNQZ24".to_string(),
                    side: OrderSide::Sell,
                    quantity: 1,
                    order_type: OrderType::Market,
                    price: Some(tick.price),
                    timestamp: Utc::now(),
                    id: format!("ORDER_{}", self.order_count),
                })
            }
        }

        fn on_order_fill(&mut self, _fill: &crate::strategy::traits::OrderFill) {
            // Update internal state based on fill
        }

        fn get_parameters(&self) -> &StrategyConfig {
            &self.config
        }

        fn reset(&mut self) {
            self.order_count = 0;
            self.position = Position::Flat;
        }
        
        fn get_position(&self) -> &Position {
            &self.position
        }

        fn get_metrics(&self) -> StrategyMetrics {
            StrategyMetrics {
                total_signals: self.order_count,
                profitable_signals: self.order_count / 2,
                average_holding_time_ms: 60000,
                sharpe_ratio: 1.5,
                max_drawdown: Decimal::from_str("0.05").unwrap(),
                win_rate: 0.55,
            }
        }
    }

    #[test]
    fn test_strategy_on_tick() {
        let mut strategy = MockStrategy::new();
        let tick = create_test_tick("18500.25", 10);
        let context = create_test_context();

        let order = strategy.on_tick(&tick, &context);
        assert!(order.is_some());
        
        let order = order.unwrap();
        assert_eq!(order.side, OrderSide::Buy);
        assert_eq!(order.quantity, 1);
    }

    #[test]
    fn test_strategy_alternating_orders() {
        let mut strategy = MockStrategy::new();
        let tick = create_test_tick("18500.25", 10);
        let context = create_test_context();

        // First order should be buy
        let order1 = strategy.on_tick(&tick, &context);
        assert!(order1.is_some());
        assert_eq!(order1.unwrap().side, OrderSide::Buy);

        // Second order should be sell
        let order2 = strategy.on_tick(&tick, &context);
        assert!(order2.is_some());
        assert_eq!(order2.unwrap().side, OrderSide::Sell);
    }

    #[test]
    fn test_strategy_reset() {
        let mut strategy = MockStrategy::new();
        let tick = create_test_tick("18500.25", 10);
        let context = create_test_context();

        // Generate some orders
        strategy.on_tick(&tick, &context);
        strategy.on_tick(&tick, &context);
        assert_eq!(strategy.order_count, 2);

        // Reset should clear state
        strategy.reset();
        assert_eq!(strategy.order_count, 0);
    }

    #[test]
    fn test_strategy_metrics() {
        let mut strategy = MockStrategy::new();
        let tick = create_test_tick("18500.25", 10);
        let context = create_test_context();

        // Generate some orders
        for _ in 0..10 {
            strategy.on_tick(&tick, &context);
        }

        let metrics = strategy.get_metrics();
        assert_eq!(metrics.total_signals, 10);
        assert_eq!(metrics.profitable_signals, 5);
        assert!(metrics.win_rate > 0.5);
    }

    #[test]
    fn test_order_fill_handling() {
        let mut strategy = MockStrategy::new();
        
        let fill = OrderFill {
            order_id: "ORDER_1".to_string(),
            timestamp: Utc::now(),
            price: Decimal::from_str("18500.25").unwrap(),
            quantity: 1,
            side: OrderSide::Buy,
            commission: Decimal::from_str("1.00").unwrap(),
        };

        strategy.on_order_fill(&fill);
        // Strategy should update its internal state
    }

    // Helper functions
    fn create_test_tick(price: &str, volume: i32) -> TickData {
        TickData {
            timestamp: 1234567890,
            price: Decimal::from_str(price).unwrap(),
            volume,
            mdt: crate::MarketDataType::Trade,
            level: crate::DataLevel::L1,
            operation: 255,  // None
            depth: 255,  // None
            market_maker_len: 0,  // No market maker
            contract_month_len: 4,  // "0624" length
            // Note: The actual contract data would be stored in memory after this struct
        }
    }

    fn create_test_context() -> StrategyContext {
        StrategyContext {
            current_position: Position::Flat,
            order_book: OrderBookState {
                bid_levels: vec![],
                ask_levels: vec![],
                last_update: Utc::now(),
            },
            portfolio_value: Decimal::from(100000),
            available_capital: Decimal::from(100000),
            current_time: Utc::now(),
        }
    }
}