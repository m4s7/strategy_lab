import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from ..database.database import get_db
from ..api.system import get_system_status, get_system_stats
from .connection_manager import connection_manager

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Manages real-time updates for dashboard components."""
    
    def __init__(self):
        self.update_interval = 30  # seconds
        self.running = False
        self._task = None
    
    async def start(self):
        """Start the dashboard update background task."""
        if self.running:
            return
            
        self.running = True
        self._task = asyncio.create_task(self._update_loop())
        logger.info("Dashboard updater started")
    
    async def stop(self):
        """Stop the dashboard update background task."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Dashboard updater stopped")
    
    async def _update_loop(self):
        """Main update loop that broadcasts dashboard data."""
        while self.running:
            try:
                # Get system status and stats
                system_status = await get_system_status()
                system_stats = await get_system_stats(next(get_db()))
                
                # Broadcast system status update
                await connection_manager.broadcast_to_topic(
                    'system:status',
                    {
                        'type': 'system_status',
                        'payload': system_status,
                        'timestamp': datetime.now().isoformat()
                    }
                )
                
                # Broadcast system stats update
                await connection_manager.broadcast_to_topic(
                    'system:stats',
                    {
                        'type': 'system_stats',
                        'payload': system_stats,
                        'timestamp': datetime.now().isoformat()
                    }
                )
                
                logger.debug("Dashboard updates broadcasted")
                
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
            
            # Wait for next update interval
            await asyncio.sleep(self.update_interval)
    
    async def broadcast_backtest_update(self, backtest_data: Dict[str, Any]):
        """Broadcast backtest-related updates to dashboard subscribers."""
        await connection_manager.broadcast_to_topic(
            'backtest:all',
            {
                'type': 'backtest_updated',
                'payload': backtest_data,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def broadcast_backtest_created(self, backtest_data: Dict[str, Any]):
        """Broadcast new backtest creation to dashboard."""
        await connection_manager.broadcast_to_topic(
            'backtest:all',
            {
                'type': 'backtest_created',
                'payload': backtest_data,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Also broadcast to active backtests topic if it's active
        if backtest_data.get('status') in ['pending', 'running']:
            await connection_manager.broadcast_to_topic(
                'backtest:active',
                {
                    'type': 'backtest_created',
                    'payload': backtest_data,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    async def broadcast_backtest_progress(self, backtest_id: str, progress: Dict[str, Any]):
        """Broadcast backtest progress updates."""
        await connection_manager.broadcast_to_topic(
            'backtest:active',
            {
                'type': 'backtest_progress',
                'payload': {
                    'backtest_id': backtest_id,
                    'progress': progress
                },
                'timestamp': datetime.now().isoformat()
            }
        )

# Global dashboard updater instance
dashboard_updater = DashboardUpdater()