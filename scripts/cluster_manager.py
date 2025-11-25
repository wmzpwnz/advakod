#!/usr/bin/env python3
"""
Менеджер кластера для ИИ-Юрист
Управление балансировкой нагрузки и мониторингом серверов
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServerStatus:
    """Статус сервера"""
    server_id: str
    url: str
    is_healthy: bool
    response_time: float
    last_check: datetime
    error_count: int = 0

class ClusterManager:
    """Менеджер кластера для управления серверами"""
    
    def __init__(self):
        self.servers = [
            {"id": "backend-1", "url": "http://localhost:8000", "weight": 3},
            {"id": "backend-2", "url": "http://localhost:8001", "weight": 3},
            {"id": "backend-3", "url": "http://localhost:8002", "weight": 2},
            {"id": "backend-4", "url": "http://localhost:8003", "weight": 2},
        ]
        self.server_statuses: Dict[str, ServerStatus] = {}
        self.healthy_servers: List[str] = []
        self.unhealthy_servers: List[str] = []
        
    async def check_server_health(self, server: Dict[str, Any]) -> ServerStatus:
        """Проверка здоровья сервера"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{server['url']}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return ServerStatus(
                            server_id=server["id"],
                            url=server["url"],
                            is_healthy=True,
                            response_time=response_time,
                            last_check=datetime.now(),
                            error_count=0
                        )
                    else:
                        return ServerStatus(
                            server_id=server["id"],
                            url=server["url"],
                            is_healthy=False,
                            response_time=response_time,
                            last_check=datetime.now(),
                            error_count=1
                        )
                        
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Health check failed for {server['id']}: {str(e)}")
            
            return ServerStatus(
                server_id=server["id"],
                url=server["url"],
                is_healthy=False,
                response_time=response_time,
                last_check=datetime.now(),
                error_count=1
            )
    
    async def check_all_servers(self):
        """Проверка всех серверов"""
        logger.info("Checking all servers health...")
        
        tasks = [self.check_server_health(server) for server in self.servers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.healthy_servers.clear()
        self.unhealthy_servers.clear()
        
        for result in results:
            if isinstance(result, ServerStatus):
                self.server_statuses[result.server_id] = result
                
                if result.is_healthy:
                    self.healthy_servers.append(result.server_id)
                else:
                    self.unhealthy_servers.append(result.server_id)
            else:
                logger.error(f"Health check error: {result}")
        
        logger.info(f"Healthy servers: {len(self.healthy_servers)}")
        logger.info(f"Unhealthy servers: {len(self.unhealthy_servers)}")
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Получение статистики серверов"""
        stats = {
            "total_servers": len(self.servers),
            "healthy_servers": len(self.healthy_servers),
            "unhealthy_servers": len(self.unhealthy_servers),
            "health_percentage": (len(self.healthy_servers) / len(self.servers)) * 100,
            "servers": {}
        }
        
        for server_id, status in self.server_statuses.items():
            stats["servers"][server_id] = {
                "url": status.url,
                "is_healthy": status.is_healthy,
                "response_time": status.response_time,
                "last_check": status.last_check.isoformat(),
                "error_count": status.error_count
            }
        
        return stats
    
    async def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Получение статистики балансировщика нагрузки"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8080/nginx_status") as response:
                    if response.status == 200:
                        text = await response.text()
                        # Парсинг nginx status
                        lines = text.strip().split('\n')
                        stats = {}
                        
                        for line in lines:
                            if ':' in line:
                                key, value = line.split(':', 1)
                                stats[key.strip()] = value.strip()
                        
                        return stats
                    else:
                        return {"error": f"HTTP {response.status}"}
                        
        except Exception as e:
            return {"error": str(e)}
    
    async def restart_unhealthy_servers(self):
        """Перезапуск нездоровых серверов"""
        if not self.unhealthy_servers:
            logger.info("No unhealthy servers to restart")
            return
        
        logger.info(f"Restarting unhealthy servers: {self.unhealthy_servers}")
        
        # В реальном приложении здесь будет команда для перезапуска Docker контейнеров
        # subprocess.run(["docker", "restart", container_name])
        
        for server_id in self.unhealthy_servers:
            logger.info(f"Restarting {server_id}...")
            # Имитация перезапуска
            await asyncio.sleep(1)
    
    async def scale_servers(self, target_count: int):
        """Масштабирование серверов"""
        current_count = len(self.healthy_servers)
        
        if target_count > current_count:
            # Увеличиваем количество серверов
            logger.info(f"Scaling up from {current_count} to {target_count} servers")
            # В реальном приложении здесь будет создание новых контейнеров
        elif target_count < current_count:
            # Уменьшаем количество серверов
            logger.info(f"Scaling down from {current_count} to {target_count} servers")
            # В реальном приложении здесь будет остановка контейнеров
        else:
            logger.info("No scaling needed")
    
    async def monitor_cluster(self, interval: int = 30):
        """Мониторинг кластера"""
        logger.info("Starting cluster monitoring...")
        
        while True:
            try:
                await self.check_all_servers()
                
                # Получаем статистику
                server_stats = self.get_server_stats()
                lb_stats = await self.get_load_balancer_stats()
                
                # Логируем статистику
                logger.info(f"Cluster stats: {json.dumps(server_stats, indent=2)}")
                logger.info(f"Load balancer stats: {json.dumps(lb_stats, indent=2)}")
                
                # Автоматическое масштабирование
                health_percentage = server_stats["health_percentage"]
                if health_percentage < 50:
                    logger.warning("Low health percentage, scaling up...")
                    await self.scale_servers(len(self.servers) + 1)
                elif health_percentage > 90 and len(self.healthy_servers) > 2:
                    logger.info("High health percentage, scaling down...")
                    await self.scale_servers(len(self.healthy_servers) - 1)
                
                # Перезапуск нездоровых серверов
                if self.unhealthy_servers:
                    await self.restart_unhealthy_servers()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {str(e)}")
                await asyncio.sleep(interval)
    
    async def get_cluster_health(self) -> Dict[str, Any]:
        """Получение общего здоровья кластера"""
        await self.check_all_servers()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy" if len(self.healthy_servers) > len(self.unhealthy_servers) else "unhealthy",
            "stats": self.get_server_stats(),
            "load_balancer": await self.get_load_balancer_stats()
        }

async def main():
    """Основная функция"""
    cluster_manager = ClusterManager()
    
    # Проверяем здоровье кластера
    health = await cluster_manager.get_cluster_health()
    print(json.dumps(health, indent=2))
    
    # Запускаем мониторинг
    await cluster_manager.monitor_cluster()

if __name__ == "__main__":
    asyncio.run(main())
