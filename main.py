"""
Главен входен пункт за IoT IIoT Intelligence Platform
Стартира всички микросервизи и управлява lifecycle-а им
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from src.industry_4_0.cnc_ai_pipeline import main as ai_pipeline_main

# Import services
from src.core.fastapi_backend import app as fastapi_app
from src.infrastructure.kafka_ai_integration import main as kafka_main
from src.core.module_integration_service import ModuleIntegrationService

# Optional services (check if available)
try:
    from src.ai_ml.chatbot_service import ChatbotService

    CHATBOT_AVAILABLE = True
except ImportError:
    CHATBOT_AVAILABLE = False
    logger.warning("Chatbot service not available")

try:
    from src.ai_ml.forecasting_service import ForecastingService

    FORECASTING_AVAILABLE = True
except ImportError:
    FORECASTING_AVAILABLE = False
    logger.warning("Forecasting service not available")

try:
    from src.industry_4_0.machine_performance_service import MachinePerformanceService

    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False
    logger.warning("Machine performance service not available")

try:
    from src.gui.energy_monitoring_dashboard import EnergyMonitoringDashboard

    ENERGY_MONITORING_AVAILABLE = True
except ImportError:
    ENERGY_MONITORING_AVAILABLE = False
    logger.warning("Energy monitoring service not available")

# Import improved modules
try:
    from src.infrastructure.adaptive_rate_limiter_qos_manager import AdaptiveRateLimiterQoSManager
    from src.sustainability.energy_optimization_ai import EnergyOptimizationAI

    IMPROVED_MODULES_AVAILABLE = True
except ImportError as e:
    IMPROVED_MODULES_AVAILABLE = False
    logger.warning(f"Improved modules not available: {e}")

# Import energy trading modules
try:
    from src.gui.energy_trading_gui import EnergyTradingGUI
    from src.industry_4_0.energy_trading_marketplace import EnergyTradingMarketplace

    ENERGY_TRADING_AVAILABLE = True
except ImportError as e:
    ENERGY_TRADING_AVAILABLE = False
    logger.warning(f"Energy trading modules not available: {e}")

# Import AR/VR modules
try:
    from src.ar_vr_maintenance_guide import ARVRMaintenanceGuide
    from src.gui.mixed_reality_dashboard import MixedRealityDashboard
    from src.gui.vr_training_simulator import VRTrainingSimulator

    ARVR_AVAILABLE = True
except ImportError as e:
    ARVR_AVAILABLE = False
    logger.warning(f"AR/VR modules not available: {e}")


class PlatformOrchestrator:
    """Оркестратор за управление на всички услуги в платформата"""

    def __init__(self):
        self.services = []
        self.tasks = []
        self.shutdown_event = asyncio.Event()

        # Module integration service
        self.module_integration = ModuleIntegrationService()

    async def start_services(self):
        """Стартира всички услуги"""

        logger.info("🚀 Starting IoT IIoT Intelligence Platform...")

        # 1. Start FastAPI Backend
        logger.info("Starting FastAPI Backend...")
        import uvicorn
        from fastapi import FastAPI

        from src.core.config import settings

        # Create server config
        config = uvicorn.Config(
            fastapi_app,
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level.lower(),
            workers=settings.workers,
        )
        server = uvicorn.Server(config)

        # Start FastAPI in background task
        fastapi_task = asyncio.create_task(server.serve())
        self.tasks.append(fastapi_task)
        logger.info(f"✅ FastAPI Backend started on {settings.host}:{settings.port}")

        # 2. Start Kafka AI Integration
        logger.info("Starting Kafka AI Integration...")
        kafka_task = asyncio.create_task(kafka_main())
        self.tasks.append(kafka_task)
        logger.info("✅ Kafka AI Integration started")

        # 3. Start AI Pipeline Demo (optional)
        logger.info("Starting AI Pipeline Demo...")
        ai_task = asyncio.create_task(ai_pipeline_main())
        self.tasks.append(ai_task)
        logger.info("✅ AI Pipeline Demo started")

        # 4. Start optional services
        if CHATBOT_AVAILABLE:
            logger.info("Starting Chatbot Service...")
            chatbot_service = ChatbotService()
            chatbot_task = asyncio.create_task(chatbot_service.start())
            self.tasks.append(chatbot_task)
            logger.info("✅ Chatbot Service started")

        if FORECASTING_AVAILABLE:
            logger.info("Starting Forecasting Service...")
            # Forecasting service needs database connection
            import asyncpg

            from src.core.config import settings

            db_conn = await asyncpg.connect(
                user=settings.postgres_user,
                password=settings.postgres_password,
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
            )
            forecasting_service = ForecastingService(db_conn)
            forecasting_task = asyncio.create_task(
                forecasting_service.process_data_for_forecasting()
            )
            self.tasks.append(forecasting_task)
            logger.info("✅ Forecasting Service started")

        if PERFORMANCE_AVAILABLE:
            logger.info("Starting Machine Performance Service...")
            # Performance service needs database connection
            db_conn = await asyncpg.connect(
                user=settings.postgres_user,
                password=settings.postgres_password,
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
            )
            performance_service = MachinePerformanceService(db_conn)
            performance_task = asyncio.create_task(performance_service.start())
            self.tasks.append(performance_task)
            logger.info("✅ Machine Performance Service started")

        # Register and start improved modules
        if IMPROVED_MODULES_AVAILABLE:
            logger.info("Registering improved modules...")

            # Register Energy Optimization AI
            energy_config = {
                "baseline_consumption": 100.0,
                "optimization_threshold": 0.05,
                "monitoring_interval": 300,
            }
            energy_ai = EnergyOptimizationAI(config=energy_config)
            await self.module_integration.register_module(
                "energy_optimization_ai", energy_ai, energy_config
            )
            await self.module_integration.activate_module("energy_optimization_ai")
            logger.info("✅ Energy Optimization AI module registered and activated")

            # Register Adaptive Rate Limiter QoS Manager
            rate_limits = {"user1": 10, "user2": 5, "admin": 50}
            qos_config = {
                "adaptation_enabled": True,
                "monitoring_enabled": True,
                "max_wait_time": 30,
            }
            qos_manager = AdaptiveRateLimiterQoSManager(
                rate_limits=rate_limits, config=qos_config
            )
            await self.module_integration.register_module(
                "adaptive_rate_limiter_qos", qos_manager, qos_config
            )
            await self.module_integration.activate_module("adaptive_rate_limiter_qos")
            logger.info("✅ Adaptive Rate Limiter QoS Manager registered and activated")

            # Create integrated processing pipeline
            await self.module_integration.create_processing_pipeline(
                "main_processing_pipeline",
                ["energy_optimization_ai", "adaptive_rate_limiter_qos"],
                {"pipeline_type": "integrated_ai_processing"},
            )
            logger.info("✅ Main processing pipeline created")

        # Start Energy Trading Marketplace
        if ENERGY_TRADING_AVAILABLE:
            logger.info("Starting Energy Trading Marketplace...")

            # Initialize marketplace
            energy_marketplace = EnergyTradingMarketplace()

            # Start market monitoring
            await energy_marketplace.start_market_monitoring()

            # Initialize GUI
            energy_gui = EnergyTradingGUI(energy_marketplace)

            # Register marketplace as a service
            await self.module_integration.register_module(
                "energy_trading_marketplace",
                energy_marketplace,
                {"service_type": "marketplace"},
            )
            await self.module_integration.activate_module("energy_trading_marketplace")

            # Register GUI as a service
            await self.module_integration.register_module(
                "energy_trading_gui", energy_gui, {"service_type": "gui"}
            )
            await self.module_integration.activate_module("energy_trading_gui")

            logger.info("✅ Energy Trading Marketplace started")
            logger.info("🌐 Energy Trading GUI: http://localhost:8000/energy-trading")

        # Start AR/VR Services
        if ARVR_AVAILABLE:
            logger.info("Starting AR/VR Services...")

            # Initialize AR/VR Maintenance Guide
            ar_vr_guide = ARVRMaintenanceGuide()
            await self.module_integration.register_module(
                "ar_vr_maintenance_guide", ar_vr_guide, {"service_type": "ar_vr"}
            )
            await self.module_integration.activate_module("ar_vr_maintenance_guide")

            # Initialize VR Training Simulator
            vr_simulator = VRTrainingSimulator()
            await self.module_integration.register_module(
                "vr_training_simulator", vr_simulator, {"service_type": "training"}
            )
            await self.module_integration.activate_module("vr_training_simulator")

            # Initialize Mixed Reality Dashboard
            mr_dashboard = MixedRealityDashboard()
            await self.module_integration.register_module(
                "mixed_reality_dashboard", mr_dashboard, {"service_type": "dashboard"}
            )
            await self.module_integration.activate_module("mixed_reality_dashboard")

            logger.info("✅ AR/VR Services started")
            logger.info("🥽 AR/VR Maintenance: http://localhost:8000/ar-vr/maintenance")
            logger.info("🎓 VR Training: http://localhost:8000/vr/training")
            logger.info("📊 MR Dashboard: http://localhost:8000/mr/dashboard")

        logger.info("🎉 All services started successfully!")
        logger.info("📊 Platform Status: Operational")
        logger.info("🌐 FastAPI: http://localhost:8000")
        logger.info("⚡ Energy Trading: http://localhost:8000/energy-trading/dashboard")
        logger.info("📊 Grafana: http://localhost:3000")
        logger.info("🔍 Kibana: http://localhost:5601")
        if IMPROVED_MODULES_AVAILABLE:
            logger.info("🤖 AI Modules: Active and Integrated")
        if ENERGY_TRADING_AVAILABLE:
            logger.info("🔋 Energy Trading Marketplace: Active")

    async def stop_services(self):
        """Спира всички услуги gracefully"""
        logger.info("🛑 Shutting down platform...")

        # Signal shutdown
        self.shutdown_event.set()

        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)

        logger.info("✅ All services stopped")

    async def health_check(self) -> Dict[str, Any]:
        """Проверява здравето на платформата"""
        health_status = {
            "platform": "IoT IIoT Intelligence Platform",
            "status": "healthy",
            "services": {},
            "modules": {},
        }

        # Check FastAPI
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=5.0)
                health_status["services"]["fastapi"] = (
                    "healthy" if response.status_code == 200 else "unhealthy"
                )
        except:
            health_status["services"]["fastapi"] = "unreachable"

        # Check Kafka (simplified)
        try:
            from kafka import KafkaAdminClient

            admin_client = KafkaAdminClient(bootstrap_servers=["localhost:9092"])
            admin_client.close()
            health_status["services"]["kafka"] = "healthy"
        except:
            health_status["services"]["kafka"] = "unreachable"

        # Check module integration service
        try:
            module_health = await self.module_integration.get_integrated_health_status()
            health_status["modules"] = module_health
        except Exception as e:
            health_status["modules"] = {"status": "error", "error": str(e)}

        # Overall status determination
        unhealthy_services = [
            s for s in health_status["services"].values() if s != "healthy"
        ]

        # Check module health
        module_status = health_status["modules"].get("overall_status", "unknown")
        if module_status not in ["healthy", "unknown"]:
            unhealthy_services.append("modules")

        if unhealthy_services:
            health_status["status"] = "degraded"

        return health_status

    async def run(self):
        """Главен lifecycle на платформата"""

        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop_services())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Start all services
            await self.start_services()

            # Periodic health checks
            while not self.shutdown_event.is_set():
                health = await self.health_check()
                if health["status"] == "healthy":
                    logger.info("💚 Platform health: OK")
                else:
                    logger.warning(f"💛 Platform health: {health['status']}")

                await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Platform error: {e}")
            await self.stop_services()
            sys.exit(1)


async def main():
    """Главна функция"""
    orchestrator = PlatformOrchestrator()

    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Platform shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await orchestrator.stop_services()


if __name__ == "__main__":
    # Run platform
    asyncio.run(main())
