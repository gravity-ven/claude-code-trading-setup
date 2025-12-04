#!/usr/bin/env python3
"""
AGENT HEALTH MONITORING API ENDPOINTS
====================================

Provides REST API endpoints for monitoring data point agent health,
system status, and real-time data from agents.

Endpoints:
- GET /api/agents/health - System-wide health status
- GET /api/agents/status/{agent_id} - Individual agent status
- GET /api/agents/metrics - System performance metrics
- GET /api/data/point/{symbol} - Get data from specific agent
- WebSocket /ws/health - Real-time health updates
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
import sys
from pathlib import Path
from aiohttp import web, WSMsgType
import aiohttp_cors

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_point_master_orchestrator import DataPointMasterOrchestrator
from data_points.spy_agent import SPYAgent
from data_points.qqq_agent import QQQAgent
from data_points.btc_usd_agent import BTCUSDAgent
from data_points.vix_agent import VIXAgent
from data_points.treasury_10y_agent import Treasury10YAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentHealthAPI:
    """API server for agent health monitoring"""

    def __init__(self, port: int = 8890):
        self.port = port
        self.app = web.Application()
        self.orchestrator = None
        self.websocket_clients = set()
        
        # Setup CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Setup routes
        self._setup_routes()
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)

    def _setup_routes(self):
        """Setup API routes"""
        # Health monitoring endpoints
        self.app.router.add_get('/api/agents/health', self.system_health)
        self.app.router.add_get('/api/agents/status/{agent_id}', self.agent_status)
        self.app.router.add_get('/api/agents/metrics', self.system_metrics)
        self.app.router.add_get('/api/agents/list', self.list_agents)
        
        # Data access endpoints  
        self.app.router.add_get('/api/data/point/{symbol}', self.get_data_point)
        self.app.router.add_get('/api/data/points', self.get_all_data_points)
        self.app.router.add_get('/api/data/market-summary', self.market_summary)
        
        # Control endpoints
        self.app.router.add_post('/api/agents/restart/{agent_id}', self.restart_agent)
        self.app.router.add_get('/api/orchestrator/status', self.orchestrator_status)
        
        # WebSocket for real-time updates
        self.app.router.add_get('/ws/health', self.websocket_handler)

    async def start_orchestrator(self):
        """Start the master orchestrator if not running"""
        if not self.orchestrator:
            self.orchestrator = create_orchestrator()
            
            # Start orchestrator in background task
            asyncio.create_task(self.orchestrator.start())
            
            # Wait a moment for agents to initialize
            await asyncio.sleep(2)

    def create_orchestrator(self):
        """Create and initialize orchestrator with all agents"""
        orchestrator = DataPointMasterOrchestrator()
        
        # Register all data point agents
        agents = {
            'spy': SPYAgent(),
            'qqq': QQQAgent(),
            'btc_usd': BTCUSDAgent(),
            'vix': VIXAgent(),
            'treasury_10y': Treasury10YAgent()
        }
        
        for agent_name, agent in agents.items():
            orchestrator.register_agent(agent)
            
        logger.info(f"📊 Registered {len(agents)} data point agents")
        return orchestrator

    async def system_health(self, request):
        """Get system-wide health status"""
        await self.start_orchestrator()
        
        health = await self.orchestrator.get_system_health()
        
        # Add API-specific information
        health['api'] = {
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'websocket_clients': len(self.websocket_clients)
        }
        
        return web.json_response(health)

    async def agent_status(self, request):
        """Get individual agent status"""
        await self.start_orchestrator()
        
        agent_id = request.match_info['agent_id']
        
        if agent_id not in self.orchestrator.agents:
            return web.json_response(
                {'error': f'Agent {agent_id} not found'}, 
                status=404
            )
        
        agent = self.orchestrator.agents[agent_id]
        health = agent.get_health_status()
        
        # Add additional agent details
        health['details'] = {
            'data_point': agent.data_point,
            'data_type': agent.data_type,
            'primary_sources': agent.primary_sources,
            'fallback_sources': agent.fallback_sources,
            'current_source': agent.current_source
        }
        
        # Add specialized analysis if available
        if agent_id == 'spy_agent':
            health['tech_analysis'] = agent.get_detailed_health()
        elif agent_id == 'qqq_agent':
            health['tech_analysis'] = agent.get_tech_sector_health()
        elif agent_id == 'btc_usd_agent':
            health['crypto_analysis'] = agent.get_crypto_market_analysis()
        elif agent_id == 'vix_agent':
            health['volatility_analysis'] = agent.get_volatility_analysis()
        elif agent_id == 'treasury_10y_agent':
            health['yield_analysis'] = agent.get_yield_analysis()
        
        return web.json_response(health)

    async def system_metrics(self, request):
        """Get system performance metrics"""
        await self.start_orchestrator()
        
        system_health = await self.orchestrator.get_system_health()
        
        # Calculate derived metrics
        total_fetches = sum(a['total_fetches'] for a in system_health['agents'].values())
        total_successes = sum(a['successful_fetches'] for a in system_health['agents'].values())
        total_failures = sum(a['consecutive_failures'] for a in system_health['agents'].values())
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'uptime_minutes': system_health['system_uptime_minutes'],
                'total_agents': system_health['total_agents'],
                'active_agents': system_health['active_agents'],
                'critical_agents': system_health['critical_agents'],
                'overall_success_rate': system_health['overall_success_rate']
            },
            'performance': {
                'total_fetches': total_fetches,
                'successful_fetches': total_successes,
                'total_failures': total_failures,
                'success_rate': (total_successes / max(1, total_fetches)) * 100
            },
            'data_quality': {
                'average_quality_score': sum(
                    a.get('data_quality_score', 0) 
                    for a in system_health['agents'].values()
                ) / max(1, len(system_health['agents'])),
                'agents_with_high_quality': len([
                    a for a in system_health['agents'].values()
                    if a.get('data_quality_score', 0) > 80
                ])
            }
        }
        
        return web.json_response(metrics)

    async def list_agents(self, request):
        """List all registered agents with basic info"""
        await self.start_orchestrator()
        
        agents = []
        for agent_id, agent in self.orchestrator.agents.items():
            health = agent.get_health_status()
            
            agents.append({
                'agent_id': agent_id,
                'data_point': agent.data_point,
                'data_type': agent.data_type,
                'health_status': health['health_status'],
                'consecutive_failures': health['consecutive_failures'],
                'last_successful_fetch': health['last_successful_fetch'],
                'uptime_percentage': health['uptime_percentage']
            })
        
        return web.json_response({
            'agents': agents,
            'total_count': len(agents),
            'timestamp': datetime.now().isoformat()
        })

    async def get_data_point(self, request):
        """Get data from specific agent"""
        await self.start_orchestrator()
        
        symbol = request.match_info['symbol'].upper()
        
        # Find the agent responsible for this symbol
        target_agent = None
        for agent in self.orchestrator.agents.values():
            if agent.data_point == symbol:
                target_agent = agent
                break
        
        if not target_agent:
            return web.json_response(
                {'error': f'No agent found for symbol {symbol}'}, 
                status=404
            )
        
        # Get cached data from agent
        data = target_agent.get_cached_data()
        if data:
            # Add metadata
            data['agent_info'] = {
                'agent_id': target_agent.agent_id,
                'health_status': target_agent.health_status,
                'last_fetch': target_agent.metrics['last_fetch'],
                'quality_score': data.get('quality_score', 0)
            }
            return web.json_response({'data': data})
        else:
            # Try fetching fresh data
            fresh_data = await target_agent.fetch_data()
            if fresh_data:
                return web.json_response({'data': fresh_data})
            else:
                return web.json_response(
                    {'error': f'No data available for {symbol}'}, 
                    status=503
                )

    async def get_all_data_points(self, request):
        """Get data from all agents"""
        await self.start_orchestrator()
        
        all_data = {}
        errors = []
        
        for agent in self.orchestrator.agents.values():
            try:
                data = agent.get_cached_data()
                if data:
                    all_data[agent.data_point] = {
                        'data': data,
                        'health': agent.get_health_status()
                    }
                else:
                    errors.append(f"No data for {agent.data_point}")
            except Exception as e:
                errors.append(f"Error getting {agent.data_point}: {e}")
        
        return web.json_response({
            'data_points': all_data,
            'total_points': len(all_data),
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        })

    async def market_summary(self, request):
        """Get market summary from key agents"""
        await self.start_orchestrator()
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'indices': {},
            'market_sentiment': 'UNKNOWN'
        }
        
        # Get data from key market agents
        key_agents = {
            'SPY': self.orchestrator.agents.get('spy_agent'),
            'QQQ': self.orchestrator.agents.get('qqq_agent'),
            'VIX': self.orchestrator.agents.get('vix_agent'),
            'DGS10': self.orchestrator.agents.get('treasury_10y_agent'),
            'BTC-USD': self.orchestrator.agents.get('btc_usd_agent')
        }
        
        market_changes = []
        
        for symbol, agent in key_agents.items():
            if not agent:
                continue
                
            data = agent.get_cached_data()
            if data:
                summary['indices'][symbol] = {
                    'price': data.get('price'),
                    'change_percent': data.get('change_percent', 0),
                    'source': data.get('source'),
                    'timestamp': data.get('timestamp')
                }
                
                if data.get('change_percent') is not None:
                    market_changes.append(data['change_percent'])
        
        # Calculate market sentiment
        if market_changes:
            avg_change = sum(market_changes) / len(market_changes)
            if avg_change > 0.5:
                summary['market_sentiment'] = 'BULLISH'
            elif avg_change < -0.5:
                summary['market_sentiment'] = 'BEARISH'
            else:
                summary['market_sentiment'] = 'NEUTRAL'
            
            summary['average_change'] = round(avg_change, 2)
        
        return web.json_response(summary)

    async def restart_agent(self, request):
        """Restart a specific agent"""
        await self.start_orchestrator()
        
        agent_id = request.match_info['agent_id']
        
        if agent_id not in self.orchestrator.agents:
            return web.json_response(
                {'error': f'Agent {agent_id} not found'}, 
                status=404
            )
        
        # Note: This is a simplified restart implementation
        # In practice, you'd need to gently stop and restart the agent task
        
        return web.json_response({
            'message': f'Restart requested for {agent_id}',
            'status': 'queued'
        })

    async def orchestrator_status(self, request):
        """Get orchestrator status"""
        await self.start_orchestrator()
        
        status = {
            'status': 'running',
            'agents_count': len(self.orchestrator.agents),
            'system_uptime': (datetime.now() - self.orchestrator.system_start_time).total_seconds() / 60,
            'websocket_clients': len(self.websocket_clients),
            'memory_usage': 'N/A'  # Could add memory monitoring
        }
        
        return web.json_response(status)

    async def websocket_handler(self, request):
        """WebSocket handler for real-time health updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_clients.add(ws)
        logger.info(f"New WebSocket client connected (total: {len(self.websocket_clients)})")
        
        try:
            # Send initial health status
            if self.orchestrator:
                health = await self.orchestrator.get_system_health()
                await ws.send_str(json.dumps({
                    'type': 'health_update',
                    'data': health,
                    'timestamp': datetime.now().isoformat()
                }))
            
            # Keep connection alive and handle messages periodically
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        message = json.loads(msg.data)
                        
                        if message.get('type') == 'get_health':
                            # Client requesting current health
                            if self.orchestrator:
                                health = await self.orchestrator.get_system_health()
                                await ws.send_str(json.dumps({
                                    'type': 'health_update',
                                    'data': health,
                                    'timestamp': datetime.now().isoformat()
                                }))
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON'
                        }))
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            self.websocket_clients.discard(ws)
            logger.info(f"WebSocket client disconnected (total: {len(self.websocket_clients)})")
        
        return ws

    async def broadcast_health_update(self):
        """Broadcast health update to all WebSocket clients"""
        if not self.orchestrator or not self.websocket_clients:
            return
        
        try:
            health = await self.orchestrator.get_system_health()
            message = json.dumps({
                'type': 'health_update',
                'data': health,
                'timestamp': datetime.now().isoformat()
            })
            
            # Send to all connected clients
            disconnected = set()
            for client in self.websocket_clients:
                try:
                    await client.send_str(message)
                except ConnectionResetError:
                    disconnected.add(client)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket client: {e}")
                    disconnected.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected
            
        except Exception as e:
            logger.error(f"Error broadcasting health update: {e}")

    async def start(self):
        """Start the API server"""
        logger.info(f"🚀 Starting Agent Health API on port {self.port}")
        
        # Start health update broadcaster
        asyncio.create_task(self.health_update_broadcaster())
        
        # Create and start orchestrator
        await self.start_orchestrator()
        
        # Start the web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"✅ Agent Health API running on http://localhost:{self.port}")
        logger.info("📊 Available endpoints:")
        logger.info("   GET /api/agents/health - System health")
        logger.info("   GET /api/agents/status/{agent_id} - Individual agent status")
        logger.info("   GET /api/agents/metrics - System metrics")
        logger.info("   GET /api/data/point/{symbol} - Get specific data point")
        logger.info("   GET /api/data/market-summary - Market overview")
        logger.info("   WS /ws/health - Real-time health updates")
        
        return runner

    async def health_update_broadcaster(self):
        """Periodically broadcast health updates to WebSocket clients"""
        while True:
            try:
                await asyncio.sleep(30)  # Broadcast every 30 seconds
                await self.broadcast_health_update()
            except Exception as e:
                logger.error(f"Health update broadcaster error: {e}")


async def main():
    """Main entry point"""
    api = AgentHealthAPI()
    runner = await api.start()
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("👋 Shutting down Agent Health API")
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
