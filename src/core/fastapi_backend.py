"""
FastAPI Backend за CNC Intelligence Platform
Real-time WebSocket updates + REST API
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import redis.asyncio as redis
import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from kafka import KafkaConsumer, KafkaProducer

# OpenTelemetry Tracing - Disabled for performance
# from opentelemetry import trace
# from opentelemetry.exporter.jaeger.proto.grpc import JaegerExporter
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
# from opentelemetry.sdk.resources import SERVICE_NAME, Resource
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.config import settings
from src.ai_ml.ai_trading_agent import (
    ai_trading_agent,
    create_trading_agent,
    execute_automated_trade,
    get_market_prediction,
    run_strategy_backtest,
)
# from src.alerting_system import src.infrastructure.alerting_system
from src.security.audit_logger import (
    audit_logger,
    log_api_access,
    log_security_event,
    log_user_action,
)
from src.industry_4_0.automotive_quality_control import (
    automotive_quality,
    create_apqp_project,
    generate_quality_report,
    report_non_conformance,
    submit_ppap,
    update_spc_data,
)
# from src.utils.cache_manager import src.utils.cache_manager
from src.industry_4_0.chemical_process_safety import (
    chemical_safety,
    generate_safety_report,
    perform_hazop_study,
    perform_sil_assessment,
    register_process_unit,
    report_safety_incident,
)
# from src.infrastructure.database_optimizer import DatabaseOptimizer
# from src.federated_learning_orchestrator import FederatedLearningOrchestrator
# from src.infrastructure.kafka_ai_integration import KafkaConfig  # Import KafkaConfig
# from src.core.multi_tenancy import (
#     check_tenant_limits,
#     get_current_tenant,
#     tenant_manager,
#     update_tenant_usage,
# )
# from src.utils.partnerships_integration import (
#     create_data_mapping,
#     execute_data_mapping,
#     get_partner_analytics,
#     partnerships_integration,
#     register_partner,
#     sync_partner_data,
# )
# from src.infrastructure.performance_benchmark import PerformanceBenchmark, run_benchmark
# from src.security.pharma_compliance_module import (
#     create_batch_record,
#     generate_regulatory_report,
#     perform_quality_check,
#     pharma_compliance,
#     register_gmp_area,
# )
# from src.infrastructure.rate_limiter import api_limiter
from src.infrastructure.rate_limiter import api_limiter
from src.ai_ml.federated_learning_orchestrator import FederatedLearningOrchestrator
# from src.business.sales_channel_management import (
#     create_sales_opportunity,
#     create_territory,
#     generate_sales_forecast,
#     get_sales_analytics,
#     register_channel_partner,
#     register_customer,
#     register_sales_rep,
#     sales_channel_management,
# )
# from src.security.security_audit import generate_hardening_plan, run_security_audit
from src.utils.performance_monitor import performance_monitor

# AR/VR imports
# try:
#     from ar_vr_maintenance_guide import ARVRMaintenanceGuide
#     from src.gui.mixed_reality_dashboard import MixedRealityDashboard
#     from src.gui.vr_training_simulator import VRTrainingSimulator
# 
ARVR_AVAILABLE = True
# except ImportError:
#     ARVR_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configure OpenTelemetry for Jaeger - DISABLED FOR PERFORMANCE
# resource = Resource.create(
#         SERVICE_NAME: settings.otel_service_name,
#     )
# 
# tracer_provider = TracerProvider(resource=resource)
# trace.set_tracer_provider(tracer_provider)
# 
# jaeger_exporter = JaegerExporter()
# 
# tracer_provider.add_span_processor(SimpleSpanProcessor(jaeger_exporter))

# ============================================================================
# MODELS
# ============================================================================


class MachineStatus(BaseModel):
    machine_id: str
    status: str  # normal, warning, critical
    last_update: datetime
    current_metrics: Dict


class PredictionResponse(BaseModel):
    machine_id: str
    timestamp: datetime
    anomaly_score: float
    failure_probability: float
    remaining_useful_life: float
    optimal_speed: float
    optimal_feed: float
    recommendations: List[str]
    confidence: float


class Alert(BaseModel):
    id: int
    machine_id: str
    severity: str
    type: str
    message: str
    timestamp: datetime
    acknowledged: bool = False


class HistoricalQuery(BaseModel):
    machine_ids: Optional[List[str]] = None
    start_time: datetime
    end_time: datetime
    metrics: List[str]


class OptimizationRequest(BaseModel):
    machine_id: str
    target: str  # 'efficiency', 'quality', 'speed'
    constraints: Dict


class ChatbotRequest(BaseModel):
    user_id: str
    message: str


class ChatbotResponse(BaseModel):
    user_id: str
    response: str
    timestamp: datetime


class ForecastRequest(BaseModel):
    machine_id: str
    start_time: datetime
    end_time: datetime
    interval: Optional[str] = "1 hour"  # e.g., "1 hour", "1 day"


class ForecastDataPoint(BaseModel):
    timestamp: datetime
    predicted_value: float
    # Добавете други прогнозирани метрики тук


class ForecastResponse(BaseModel):
    machine_id: str
    forecast: List[ForecastDataPoint]


class PerformanceAnalysisRequest(BaseModel):
    machine_id: str
    start_time: datetime
    end_time: datetime
    metrics: Optional[List[str]] = None


class PerformanceDataPoint(BaseModel):
    timestamp: datetime
    # Примерни метрики, които могат да бъдат върнати от анализа на производителността
    avg_cpu_usage: Optional[float] = None
    max_temperature: Optional[float] = None
    production_rate: Optional[float] = None
    # ... други метрики


class PerformanceAnalysisResponse(BaseModel):
    machine_id: str
    analysis_data: List[PerformanceDataPoint]


# ============================================================================
# AUTO ML MODELS
# ============================================================================


class AutoMLTrainingRequest(BaseModel):
    dataset_path: str
    target_column: str
    problem_type: Optional[str] = "auto"
    test_size: Optional[float] = 0.2
    cv_folds: Optional[int] = 5


class AutoMLTrainingResponse(BaseModel):
    training_id: str
    status: str
    best_model: str
    best_score: float
    training_time: float
    model_results: Dict[str, Any]
    feature_importance: Dict[str, float]


class RLTrainingRequest(BaseModel):
    episodes: Optional[int] = 1000
    max_steps: Optional[int] = 100
    parameter_ranges: Optional[Dict[str, List[float]]] = None


class RLTrainingResponse(BaseModel):
    training_id: str
    status: str
    episodes: int
    training_time: float
    average_reward: float
    best_reward: float
    best_parameters: Dict[str, float]


class NewMachine(BaseModel):
    machine_id: str
    name: str
    location: Optional[str] = None
    model: Optional[str] = None
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    status: Optional[str] = "unknown"
    metadata: Optional[Dict] = None


class Machine(NewMachine):
    open_alerts: int = 0


class SimulatedData(BaseModel):
    status: str
    anomaly_score: float
    failure_probability: float
    remaining_useful_life: float
    optimal_speed: float
    optimal_feed: float
    recommendations: List[str]
    confidence: float


# ============================================================================
# AUTHENTICATION MODELS
# ============================================================================


class User(BaseModel):
    id: int
    username: str
    email: str
    role: str  # 'admin', 'operator', 'viewer'
    is_active: bool = True


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "viewer"


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# ============================================================================
# DATABASE CONNECTION
# ============================================================================


class Database:
    def __init__(self):
        self.pool = None
        self.redis = None

    async def connect(self):
        """Initialize database connections"""
        # PostgreSQL/TimescaleDB
        self.pool = await asyncpg.create_pool(
            settings.postgres_url, min_size=10, max_size=50
        )

        # Redis
        self.redis = await redis.from_url(
            settings.redis_url, encoding="utf-8", decode_responses=True
        )

        # Initialize cache manager
        cache_manager.redis = self.redis
        await cache_manager.start_cleanup_task()

        # Initialize database optimizer
        self.optimizer = DatabaseOptimizer(self.pool)

        # Kafka Producer for chatbot requests
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        )

        # Create tables if not exist
        await self._create_tables()
        await self._create_default_admin()

    async def _create_tables(self):
        """Create necessary tables"""
        async with self.pool.acquire() as conn:
            # Predictions table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL,
                    machine_id VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    anomaly_score FLOAT,
                    failure_probability FLOAT,
                    remaining_useful_life FLOAT,
                    optimal_speed FLOAT,
                    optimal_feed FLOAT,
                    confidence FLOAT,
                    PRIMARY KEY (id, timestamp)
                );
            """
            )

            # Convert to hypertable
            try:
                await conn.execute(
                    """
                    SELECT create_hypertable('predictions', 'timestamp',
                                            if_not_exists => TRUE);
                """
                )
            except:
                pass  # Already hypertable

            # Alerts table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    machine_id VARCHAR(50) NOT NULL,
                    severity VARCHAR(20),
                    type VARCHAR(50),
                    message TEXT,
                    timestamp TIMESTAMPTZ NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_at TIMESTAMPTZ,
                    acknowledged_by VARCHAR(100)
                );
            """
            )

            # Machine metadata
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS machines (
                    machine_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100),
                    location VARCHAR(100),
                    model VARCHAR(100),
                    installation_date DATE,
                    last_maintenance DATE,
                    status VARCHAR(20),
                    metadata JSONB
                );
            """
            )

            # Users table for authentication
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(200) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_login TIMESTAMPTZ
                );
            """
            )

    async def _create_default_admin(self):
        """Create default admin user if not exists."""
        async with self.pool.acquire() as conn:
            admin_exists = await conn.fetchval(
                """
                SELECT COUNT(*) FROM users WHERE username = 'admin'
            """
            )

            if not admin_exists:
                hashed_password = get_password_hash(
                    "admin123"
                )  # TODO: Change default password
                await conn.execute(
                    """
                    INSERT INTO users (username, email, hashed_password, role)
                    VALUES ($1, $2, $3, $4)
                """,
                    "admin",
                    "admin@cnc-platform.com",
                    hashed_password,
                    "admin",
                )
                logger.info("Default admin user created")

    async def close(self):
        """Close connections"""
        if self.pool:
            await self.pool.close()
        if self.redis:
            await self.redis.close()
        if hasattr(self, "kafka_producer") and self.kafka_producer:
            self.kafka_producer.close()

        # Stop cache manager
        await cache_manager.stop_cleanup_task()


# Global database instance
db = Database()

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# ============================================================================
# AUTHENTICATION UTILITIES
# ============================================================================


def verify_password(plain_password, hashed_password):
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception

    # Verify user exists in database
    async with db.pool.acquire() as conn:
        user_row = await conn.fetchrow(
            """
            SELECT id, username, email, role, is_active
            FROM users
            WHERE username = $1 AND is_active = true
        """,
            username,
        )

        if user_row is None:
            raise credentials_exception

        user = User(**user_row)

    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """Get current user and verify admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


# ============================================================================
# WEBSOCKET MANAGER
# ============================================================================


class WebSocketManager:
    """Manage WebSocket connections и broadcast updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.kafka_consumer = None
        self.broadcast_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def start_kafka_listener(self):
        """Listen to Kafka и broadcast updates"""
        # self.kafka_consumer = KafkaConsumer(
        #     'cnc-predictions',
        #     'cnc-alerts',
        #     bootstrap_servers=['localhost:9092'],
        #     value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        #     auto_offset_reset='latest',
        #     group_id='websocket-broadcaster'
        # )

        # print("🎧 Started Kafka listener for WebSocket broadcasts")

        # Run in executor to not block
        # loop = asyncio.get_event_loop()
        # self.broadcast_task = loop.run_in_executor(None, self._kafka_loop)

    def _kafka_loop(self):
        """Kafka consumption loop"""
        for message in self.kafka_consumer:
            # Broadcast to WebSocket clients
            data = {
                "topic": message.topic,
                "data": message.value,
                "timestamp": datetime.now().isoformat(),
            }

            # Schedule broadcast in event loop
            asyncio.run_coroutine_threadsafe(
                self.broadcast(data), asyncio.get_event_loop()
            )

    async def stop(self):
        """Stop listener"""
        if self.kafka_consumer:
            self.kafka_consumer.close()


# Global WebSocket manager
ws_manager = WebSocketManager()

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting CNC Intelligence API...")
    await db.connect()
    # await ws_manager.start_kafka_listener()
    print("✅ API Ready!")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await ws_manager.stop()
    await db.close()
    print("✅ Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting middleware
app.add_middleware(api_limiter)


# Tenant isolation middleware
@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    """Tenant isolation middleware for multi-tenant support."""
    # Extract tenant from domain or header
    host = request.headers.get("host", "")
    tenant = None

    # Try domain-based tenant resolution
    if "." in host:
        domain = host.split(":")[0]  # Remove port
        tenant = tenant_manager.get_tenant_for_domain(domain)

    # Fallback to header-based
    if not tenant:
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            tenant = tenant_manager.get_tenant(tenant_header)

    # Default tenant
    if not tenant:
        tenant = tenant_manager.get_tenant("default")

    # Add tenant to request state
    request.state.tenant = tenant

    # Track API usage for tenant
    if tenant:
        await update_tenant_usage(tenant.tenant_id, "api_calls", 1)

    # Start timing for audit logging
    start_time = datetime.now()

    response = await call_next(request)

    # Audit log API access
    end_time = datetime.now()
    response_time = (end_time - start_time).total_seconds() * 1000  # ms

    # Extract user info
    user_id = None
    try:
        # Try to get user from request state or dependencies
        # This is a simplified approach - in production, use proper dependency injection
        pass
    except:
        pass

    tenant_id = tenant.tenant_id if tenant else None

    await log_api_access(
        user_id=user_id,
        tenant_id=tenant_id,
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response.status_code,
        response_time=response_time,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return response


# Instrument FastAPI for OpenTelemetry - DISABLED FOR PERFORMANCE
# FastAPIInstrumentor.instrument_app(app)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="../templates")


# Serve main dashboard
@app.get("/", response_class=HTMLResponse)
async def get_main_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """Serve the main platform dashboard HTML page."""
    try:
        # Get analytics data
        analytics_data = await get_analytics_overview(current_user)

        # Get system health
        health_data = await health_check()

        # Define all modules with their metadata
        all_modules = [
            {
                "id": "energy_monitoring_dashboard",
                "name": "Energy Monitoring Dashboard",
                "description": "Real-time visualization of energy consumption and optimization metrics",
                "icon": "fas fa-bolt",
                "status": "healthy",
                "has_gui": True,
                "category": "energy"
            },
            {
                "id": "data_quality_governance",
                "name": "Data Quality & Schema Governance",
                "description": "Automated data validation, schema management, and quality monitoring",
                "icon": "fas fa-database",
                "status": "healthy",
                "has_gui": True,
                "category": "data"
            },
            {
                "id": "model_drift_monitoring",
                "name": "Model Drift Monitoring",
                "description": "Continuous monitoring of AI model performance and drift detection",
                "icon": "fas fa-chart-line",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "centralized_feature_store",
                "name": "Centralized Feature Store",
                "description": "Feature engineering, storage, and management for ML pipelines",
                "icon": "fas fa-store",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "explainable_ai_engine",
                "name": "Explainable AI Engine",
                "description": "SHAP and LIME explanations for AI model decisions",
                "icon": "fas fa-search",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "simulation_digital_twin",
                "name": "Simulation & Digital Twin",
                "description": "Digital twin creation and simulation for predictive maintenance",
                "icon": "fas fa-cube",
                "status": "healthy",
                "has_gui": True,
                "category": "simulation"
            },
            {
                "id": "real_time_optimization",
                "name": "Real-Time Optimization (RL)",
                "description": "Reinforcement learning for real-time process optimization",
                "icon": "fas fa-rocket",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "automated_mlops_pipeline",
                "name": "Automated MLOps Pipeline",
                "description": "End-to-end ML pipeline management and deployment",
                "icon": "fas fa-cogs",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "data_lineage_audit",
                "name": "Data Lineage & Audit Trail",
                "description": "Complete data flow tracking and audit logging",
                "icon": "fas fa-route",
                "status": "healthy",
                "has_gui": True,
                "category": "data"
            },
            {
                "id": "multi_tenancy_access_control",
                "name": "Multi-Tenancy & Access Control",
                "description": "Tenant isolation and role-based access management",
                "icon": "fas fa-users",
                "status": "healthy",
                "has_gui": True,
                "category": "security"
            },
            {
                "id": "edge_ai_inference_gateway",
                "name": "Edge AI Inference Gateway",
                "description": "Edge computing and AI inference management",
                "icon": "fas fa-network-wired",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "predictive_quality_control",
                "name": "Predictive Quality Control",
                "description": "AI-driven quality prediction and defect prevention",
                "icon": "fas fa-check-double",
                "status": "healthy",
                "has_gui": True,
                "category": "quality"
            },
            {
                "id": "energy_optimization_ai",
                "name": "Energy Optimization AI",
                "description": "AI-powered energy consumption optimization",
                "icon": "fas fa-leaf",
                "status": "healthy",
                "has_gui": True,
                "category": "energy"
            },
            {
                "id": "supply_chain_inventory_predictor",
                "name": "Supply Chain & Inventory Predictor",
                "description": "Predictive analytics for supply chain and inventory management",
                "icon": "fas fa-boxes",
                "status": "healthy",
                "has_gui": True,
                "category": "supply_chain"
            },
            {
                "id": "event_replay_engine",
                "name": "Event Replay Engine",
                "description": "Historical event replay for testing and analysis",
                "icon": "fas fa-history",
                "status": "healthy",
                "has_gui": True,
                "category": "data"
            },
            {
                "id": "graphql_query_service",
                "name": "GraphQL Query Service",
                "description": "Flexible data querying with GraphQL API",
                "icon": "fas fa-code",
                "status": "healthy",
                "has_gui": True,
                "category": "data"
            },
            {
                "id": "kpi_benchmarking_engine",
                "name": "KPI Benchmarking Engine",
                "description": "Performance benchmarking and KPI comparison",
                "icon": "fas fa-trophy",
                "status": "healthy",
                "has_gui": True,
                "category": "analytics"
            },
            {
                "id": "collaborative_labeling_tool",
                "name": "Collaborative Labeling Tool",
                "description": "Human-in-the-loop data labeling and validation",
                "icon": "fas fa-users-cog",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "root_cause_analysis_engine",
                "name": "Root Cause Analysis Engine",
                "description": "Automated root cause analysis for incidents",
                "icon": "fas fa-search-plus",
                "status": "healthy",
                "has_gui": True,
                "category": "analytics"
            },
            {
                "id": "notification_intelligence",
                "name": "Notification Intelligence",
                "description": "Smart alerting and notification management",
                "icon": "fas fa-bell",
                "status": "healthy",
                "has_gui": True,
                "category": "monitoring"
            },
            {
                "id": "automated_configuration_optimizer",
                "name": "Automated Configuration Optimizer",
                "description": "AI-driven system configuration optimization",
                "icon": "fas fa-sliders-h",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "federated_learning_orchestrator",
                "name": "Federated Learning Orchestrator",
                "description": "Privacy-preserving distributed machine learning",
                "icon": "fas fa-share-alt",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "contextual_anomaly_classifier",
                "name": "Contextual Anomaly Classifier",
                "description": "Context-aware anomaly detection and classification",
                "icon": "fas fa-exclamation-triangle",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "predictive_scheduling_engine",
                "name": "Predictive Scheduling Engine",
                "description": "AI-powered production and maintenance scheduling",
                "icon": "fas fa-calendar-alt",
                "status": "healthy",
                "has_gui": True,
                "category": "planning"
            },
            {
                "id": "enduser_usage_dashboard",
                "name": "Enduser Usage Dashboard",
                "description": "User activity and platform usage analytics",
                "icon": "fas fa-user-friends",
                "status": "healthy",
                "has_gui": True,
                "category": "analytics"
            },
            {
                "id": "multi_tenant_kpi_segregation",
                "name": "Multi-Tenant KPI Segregation",
                "description": "Tenant-specific KPI management and reporting",
                "icon": "fas fa-building",
                "status": "healthy",
                "has_gui": True,
                "category": "analytics"
            },
            {
                "id": "multi_tenant_resource_management",
                "name": "Multi-Tenant Resource Management",
                "description": "Resource allocation and management across tenants",
                "icon": "fas fa-server",
                "status": "healthy",
                "has_gui": True,
                "category": "infrastructure"
            },
            {
                "id": "auto_mlworkflow_optimization_engine",
                "name": "Auto MLWorkflow Optimization Engine",
                "description": "Automated ML workflow optimization and tuning",
                "icon": "fas fa-magic",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "ai_build_prompt_aggregation_routing",
                "name": "AI Build Prompt Aggregation & Routing",
                "description": "AI prompt management and intelligent routing",
                "icon": "fas fa-route",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "fleet_management_manager",
                "name": "Fleet Management Manager",
                "description": "Comprehensive fleet asset management and monitoring",
                "icon": "fas fa-truck",
                "status": "healthy",
                "has_gui": True,
                "category": "operations"
            },
            {
                "id": "custom_ota_builder",
                "name": "Custom OTA Builder",
                "description": "Over-the-air update creation and deployment",
                "icon": "fas fa-cloud-upload-alt",
                "status": "healthy",
                "has_gui": True,
                "category": "deployment"
            },
            {
                "id": "custom_heartbeats_notifications",
                "name": "Custom Heartbeats Notifications",
                "description": "Customizable heartbeat monitoring and alerts",
                "icon": "fas fa-heartbeat",
                "status": "healthy",
                "has_gui": True,
                "category": "monitoring"
            },
            {
                "id": "marketplace_flux_factor",
                "name": "Marketplace Flux Factor",
                "description": "Dynamic marketplace pricing and flux calculations",
                "icon": "fas fa-calculator",
                "status": "healthy",
                "has_gui": True,
                "category": "marketplace"
            },
            {
                "id": "issue_tracking_tool",
                "name": "Issue Tracking Tool",
                "description": "Comprehensive issue tracking and management system",
                "icon": "fas fa-tasks",
                "status": "healthy",
                "has_gui": True,
                "category": "management"
            },
            {
                "id": "object_anatomy_ai",
                "name": "Object Anatomy AI",
                "description": "AI-powered object analysis and anatomy breakdown",
                "icon": "fas fa-microscope",
                "status": "healthy",
                "has_gui": True,
                "category": "ai"
            },
            {
                "id": "daily_progression_notifications",
                "name": "Daily Progression Notifications",
                "description": "AI-driven progress tracking and notifications",
                "icon": "fas fa-chart-bar",
                "status": "healthy",
                "has_gui": True,
                "category": "analytics"
            }
        ]

        # Prepare template data
        template_data = {
            "request": request,
            "active_machines": analytics_data.get("active_machines", 0),
            "open_alerts": analytics_data.get("open_alerts", 0),
            "active_modules": len([m for m in all_modules if m["status"] == "healthy"]),
            "avg_anomaly_score": round(analytics_data.get("avg_anomaly_score", 0), 2),
            "modules": all_modules,
            "system_health": {
                "database": health_data.get("components", {}).get("database", "unknown"),
                "redis": health_data.get("components", {}).get("redis", "unknown"),
                "kafka": health_data.get("components", {}).get("kafka", "unknown"),
                "api": "healthy" if health_data.get("status") == "healthy" else "unhealthy"
            }
        }

        return templates.TemplateResponse("main_dashboard.html", template_data)
    except Exception as e:
        logger.error(f"Failed to serve main dashboard: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


# Serve energy monitoring dashboard
@app.get("/modules/energy_monitoring_dashboard", response_class=HTMLResponse)
async def get_energy_monitoring_dashboard(current_user: User = Depends(get_current_user)):
    """Serve the energy monitoring dashboard HTML page."""
    try:
        template_path = Path(__file__).parent.parent / "templates" / "energy_monitoring_dashboard.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(
                content="<h1>Energy Monitoring Dashboard</h1><p>Template not found</p>",
                status_code=404,
            )
    except Exception as e:
        logger.error(f"Failed to serve energy monitoring dashboard: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


# Serve data quality governance dashboard
@app.get("/modules/data_quality_governance", response_class=HTMLResponse)
async def get_data_quality_governance_dashboard(current_user: User = Depends(get_current_user)):
    """Serve the data quality governance dashboard HTML page."""
    try:
        template_path = Path(__file__).parent.parent / "templates" / "data_quality_governance.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(
                content="<h1>Data Quality Governance</h1><p>Template not found</p>",
                status_code=404,
            )
    except Exception as e:
        logger.error(f"Failed to serve data quality governance dashboard: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


# Serve model drift monitoring dashboard
@app.get("/modules/model_drift_monitoring", response_class=HTMLResponse)
async def get_model_drift_monitoring_dashboard(current_user: User = Depends(get_current_user)):
    """Serve the model drift monitoring dashboard HTML page."""
    try:
        template_path = Path(__file__).parent.parent / "templates" / "model_drift_monitoring.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(
                content="<h1>Model Drift Monitoring</h1><p>Template not found</p>",
                status_code=404,
            )
    except Exception as e:
        logger.error(f"Failed to serve model drift monitoring dashboard: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


# Serve explainable AI engine dashboard
@app.get("/modules/explainable_ai_engine", response_class=HTMLResponse)
async def get_explainable_ai_engine_dashboard(current_user: User = Depends(get_current_user)):
    """Serve the explainable AI engine dashboard HTML page."""
    try:
        template_path = Path(__file__).parent.parent / "templates" / "explainable_ai_engine.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(
                content="<h1>Explainable AI Engine</h1><p>Template not found</p>",
                status_code=404,
            )
    except Exception as e:
        logger.error(f"Failed to serve explainable AI engine dashboard: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


# ============================================================================
# API ROUTERS
# ============================================================================

api_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

# Energy Monitoring API Endpoints
@api_v1.get("/energy/metrics")
async def get_energy_metrics(range: str = "24h", current_user: User = Depends(get_current_user)):
    """Get energy consumption metrics."""
    try:
        # Calculate time range
        now = datetime.now()
        if range == "1h":
            start_time = now - timedelta(hours=1)
        elif range == "6h":
            start_time = now - timedelta(hours=6)
        elif range == "24h":
            start_time = now - timedelta(hours=24)
        elif range == "7d":
            start_time = now - timedelta(days=7)
        else:
            start_time = now - timedelta(hours=24)

        async with db.pool.acquire() as conn:
            # Get total consumption
            total_result = await conn.fetchrow(
                """
                SELECT SUM(energy_consumption) as total
                FROM energy_readings
                WHERE timestamp BETWEEN $1 AND $2
                """,
                start_time, now
            )

            # Get peak consumption
            peak_result = await conn.fetchrow(
                """
                SELECT MAX(peak_power) as peak, timestamp as peak_time
                FROM energy_readings
                WHERE timestamp BETWEEN $1 AND $2
                """,
                start_time, now
            )

            # Calculate efficiency score (mock calculation)
            efficiency_score = 85 + (datetime.now().minute % 10)  # Mock dynamic value

            # Calculate cost savings (mock)
            cost_savings = 1250.50

            return {
                "total_consumption": total_result["total"] or 0,
                "peak_consumption": peak_result["peak"] or 0,
                "peak_time": peak_result["peak_time"].isoformat() if peak_result["peak_time"] else None,
                "efficiency_score": efficiency_score,
                "cost_savings": cost_savings,
                "consumption_change": "+2.3%",
                "efficiency_trend": "+5.1% improvement"
            }
    except Exception as e:
        logger.error(f"Error getting energy metrics: {e}")
        return {
            "total_consumption": 0,
            "peak_consumption": 0,
            "efficiency_score": 0,
            "cost_savings": 0
        }


@api_v1.get("/energy/consumption")
async def get_energy_consumption(range: str = "24h", current_user: User = Depends(get_current_user)):
    """Get energy consumption time series data."""
    try:
        # Calculate time range
        now = datetime.now()
        if range == "1h":
            start_time = now - timedelta(hours=1)
            interval = timedelta(minutes=5)
        elif range == "6h":
            start_time = now - timedelta(hours=6)
            interval = timedelta(minutes=30)
        elif range == "24h":
            start_time = now - timedelta(hours=24)
            interval = timedelta(hours=1)
        elif range == "7d":
            start_time = now - timedelta(days=7)
            interval = timedelta(hours=6)
        else:
            start_time = now - timedelta(hours=24)
            interval = timedelta(hours=1)

        async with db.pool.acquire() as conn:
            # Generate mock time series data
            data_points = []
            current_time = start_time
            while current_time <= now:
                # Mock consumption data with some variation
                base_consumption = 100 + (current_time.hour * 5) + (datetime.now().second % 20)
                consumption = base_consumption + (datetime.now().microsecond % 50 - 25)

                data_points.append({
                    "timestamp": current_time.isoformat(),
                    "consumption": max(0, consumption)
                })
                current_time += interval

            return data_points
    except Exception as e:
        logger.error(f"Error getting energy consumption: {e}")
        return []


@api_v1.get("/energy/equipment")
async def get_energy_equipment(current_user: User = Depends(get_current_user)):
    """Get equipment energy status."""
    try:
        # Mock equipment data
        equipment = [
            {
                "id": "machine_001",
                "name": "CNC Machine A1",
                "status": "healthy",
                "consumption": 45.2,
                "efficiency": 92
            },
            {
                "id": "machine_002",
                "name": "Assembly Line B2",
                "status": "warning",
                "consumption": 78.5,
                "efficiency": 78
            },
            {
                "id": "machine_003",
                "name": "Packaging Unit C3",
                "status": "healthy",
                "consumption": 23.1,
                "efficiency": 95
            },
            {
                "id": "machine_004",
                "name": "Quality Control D4",
                "status": "critical",
                "consumption": 12.8,
                "efficiency": 65
            }
        ]
        return equipment
    except Exception as e:
        logger.error(f"Error getting equipment data: {e}")
        return []


@api_v1.get("/energy/alerts")
async def get_energy_alerts(current_user: User = Depends(get_current_user)):
    """Get energy-related alerts."""
    try:
        # Mock alerts
        alerts = [
            {
                "id": "alert_001",
                "title": "High Energy Consumption",
                "message": "Machine A1 is consuming 25% more energy than usual",
                "severity": "high",
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat()
            },
            {
                "id": "alert_002",
                "title": "Efficiency Drop",
                "message": "Assembly Line B2 efficiency dropped below 80%",
                "severity": "medium",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
            }
        ]
        return alerts
    except Exception as e:
        logger.error(f"Error getting energy alerts: {e}")
        return []


@api_v1.post("/energy/alerts/{alert_id}/acknowledge")
async def acknowledge_energy_alert(alert_id: str, current_user: User = Depends(get_current_user)):
    """Acknowledge an energy alert."""
    try:
        # In a real implementation, this would update the database
        return {"status": "acknowledged", "alert_id": alert_id}
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@api_v1.get("/energy/recommendations")
async def get_energy_recommendations(current_user: User = Depends(get_current_user)):
    """Get energy optimization recommendations."""
    try:
        # Mock recommendations
        recommendations = [
            {
                "title": "Optimize Machine Schedule",
                "description": "Schedule high-energy operations during off-peak hours to reduce costs by 15%",
                "savings": 450
            },
            {
                "title": "Upgrade Equipment",
                "description": "Replace Machine D4 with energy-efficient model for 30% consumption reduction",
                "savings": 890
            },
            {
                "title": "Implement Load Balancing",
                "description": "Distribute workload across machines to avoid peak consumption spikes",
                "savings": 320
            }
        ]
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []


# Serve energy trading dashboard
@app.get("/energy-trading/dashboard", response_class=HTMLResponse)
async def get_energy_trading_dashboard():
    """Serve the energy trading dashboard HTML page."""
    try:
        template_path = (
            Path(__file__).parent.parent / "templates" / "energy_trading_dashboard.html"
        )
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(
                content="<h1>Energy Trading Dashboard</h1><p>Template not found</p>",
                status_code=404,
            )
    except Exception as e:
        logger.error(f"Failed to serve energy trading dashboard: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


# ============================================================================
# API ROUTERS
# ============================================================================

# Energy Trading Router
energy_router = APIRouter(prefix="/energy-trading", tags=["energy-trading"])
app.include_router(energy_router)

# AR/VR Routers
if ARVR_AVAILABLE:
    ar_router = APIRouter(prefix="/ar-vr", tags=["ar-vr"])
    vr_router = APIRouter(prefix="/vr", tags=["vr"])
    mr_router = APIRouter(prefix="/mr", tags=["mr"])

    app.include_router(ar_router)
    app.include_router(vr_router)
    app.include_router(mr_router)

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint за real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive и listen за client messages
            data = await websocket.receive_text()

            # Client може да subscribe за specific machines
            try:
                msg = json.loads(data)
                if msg.get("action") == "subscribe":
                    machine_ids = msg.get("machine_ids", [])
                    await websocket.send_json(
                        {"type": "subscription_confirmed", "machine_ids": machine_ids}
                    )
            except:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================


@api_v1.post("/auth/register", response_model=User)
async def register_user(user: UserCreate):
    """Register a new user."""
    async with db.pool.acquire() as conn:
        # Check if user already exists
        existing = await conn.fetchrow(
            """
            SELECT id FROM users WHERE username = $1 OR email = $2
        """,
            user.username,
            user.email,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered",
            )

        # Hash password
        hashed_password = get_password_hash(user.password)

        # Create user
        user_id = await conn.fetchval(
            """
            INSERT INTO users (username, email, hashed_password, role)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """,
            user.username,
            user.email,
            hashed_password,
            user.role,
        )

        # Audit log
        logger.info(f"User registered: {user.username} by {current_user.username}")

        # Security audit log
        await log_user_action(
            user_id=str(current_user.id),
            tenant_id=getattr(request.state.tenant, "tenant_id", None)
            if hasattr(request, "state")
            else None,
            action="user_register",
            resource_type="user",
            resource_id=str(user_id),
            status="success",
            details={"new_username": user.username, "role": user.role},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            severity="medium",
        )

        return User(
            id=user_id, username=user.username, email=user.email, role=user.role
        )


@api_v1.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return JWT token."""
    async with db.pool.acquire() as conn:
        user_row = await conn.fetchrow(
            """
            SELECT id, username, email, hashed_password, role, is_active
            FROM users
            WHERE username = $1
        """,
            user_credentials.username,
        )

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        user = dict(user_row)
        if not verify_password(user_credentials.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        # Update last login
        await conn.execute(
            """
            UPDATE users SET last_login = NOW() WHERE id = $1
        """,
            user["id"],
        )

        # Audit log
        logger.info(f"User login: {user_credentials.username}")

        # Security audit log
        await log_security_event(
            event_type="authentication",
            user_id=str(user["id"]),
            tenant_id=None,  # Will be set by tenant middleware
            details={"action": "login", "username": user_credentials.username},
            severity="low",
            ip_address=request.client.host if request.client else None,
        )

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]},
            expires_delta=access_token_expires,
        )

        return Token(access_token=access_token, token_type="bearer")


@api_v1.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@api_v1.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_admin_user)):
    """Get all users (admin only)."""
    async with db.pool.acquire() as conn:
        users = await conn.fetch(
            """
            SELECT id, username, email, role, is_active FROM users
        """
        )
        return [User(**dict(user)) for user in users]


@api_v1.delete("/users/{user_id}")
async def delete_user(
    user_id: int, current_user: User = Depends(get_current_admin_user)
):
    """Delete user (GDPR compliance)."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    async with db.pool.acquire() as conn:
        # Check if user exists
        user = await conn.fetchrow("SELECT username FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete user data
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)

        # Audit log
        logger.info(f"User deleted: {user['username']} by {current_user.username}")

        return {"message": "User deleted successfully"}


# ============================================================================
# REST API ENDPOINTS
# ============================================================================


@app.get("/")
async def root():
    return {
        "service": "CNC Intelligence Platform",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify API status.
    """
    return {"status": "ok", "message": "API is healthy"}


# ---------- MACHINE ENDPOINTS ----------


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "API is healthy"}


@app.get("/api/machines", response_model=List[Machine])
async def get_all_machines():
    """Get всички машини"""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT m.*,
                   COUNT(CASE WHEN a.acknowledged = false THEN 1 END) as open_alerts
            FROM machines m
            LEFT JOIN alerts a ON m.machine_id = a.machine_id
            GROUP BY m.machine_id
        """
        )
        machines_data = []
        for row in rows:
            machine_dict = dict(row)
            if "metadata" in machine_dict and isinstance(machine_dict["metadata"], str):
                machine_dict["metadata"] = json.loads(machine_dict["metadata"])
            machines_data.append(machine_dict)
        return machines_data


@app.post("/api/machines", response_model=NewMachine)
async def add_machine(
    machine: NewMachine, current_user: User = Depends(get_current_user)
):
    """Добавяне на нова машина в базата данни"""
    # Check permissions - only admin and operators can add machines
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to add machines",
        )

    async with db.pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO machines (machine_id, name, location, model, installation_date, last_maintenance, status, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
            """,
                machine.machine_id,
                machine.name,
                machine.location,
                machine.model,
                machine.installation_date,
                machine.last_maintenance,
                machine.status,
                json.dumps(machine.metadata) if machine.metadata else None,
            )
            logger.info(
                f"Machine {machine.machine_id} added by user {current_user.username}"
            )
            return machine
        except asyncpg.exceptions.UniqueViolationError:
            raise HTTPException(
                status_code=409, detail="Machine with this ID already exists"
            )
        except Exception as e:
            logger.error(f"Failed to add machine {machine.machine_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to add machine: {e}")


@app.get("/api/machines/{machine_id}/status", response_model=MachineStatus)
async def get_machine_status(machine_id: str):
    """Get real-time status на машина от Redis"""
    # Get от Redis cache
    status_key = f"machine:status:{machine_id}"
    prediction_key = f"prediction:{machine_id}"

    status = await db.redis.get(status_key)
    prediction_data = await db.redis.get(prediction_key)

    if not prediction_data:
        raise HTTPException(
            status_code=404, detail="Machine not found or no recent data"
        )

    prediction = json.loads(prediction_data)

    return MachineStatus(
        machine_id=machine_id,
        status=status or "unknown",
        last_update=datetime.fromisoformat(prediction["timestamp"]),
        current_metrics=prediction,
    )


@app.post("/api/machines/{machine_id}/simulate_data")
async def simulate_machine_data(machine_id: str, data: SimulatedData):
    """Simulate real-time data for a machine and store in Redis"""
    status_key = f"machine:status:{machine_id}"
    prediction_key = f"prediction:{machine_id}"

    # Store status
    await db.redis.set(status_key, data.status)

    # Store prediction data
    prediction_data = {
        "machine_id": machine_id,
        "timestamp": datetime.now().isoformat(),
        "anomaly_score": data.anomaly_score,
        "failure_probability": data.failure_probability,
        "remaining_useful_life": data.remaining_useful_life,
        "optimal_speed": data.optimal_speed,
        "optimal_feed": data.optimal_feed,
        "recommendations": data.recommendations,
        "confidence": data.confidence,
    }
    await db.redis.set(prediction_key, json.dumps(prediction_data))

    return {"message": f"Simulated data for {machine_id} stored successfully"}


@app.get("/api/machines/{machine_id}/prediction", response_model=PredictionResponse)
async def get_latest_prediction(machine_id: str):
    """Get последната AI предикция"""
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT machine_id, timestamp, anomaly_score, failure_probability,
                   remaining_useful_life, optimal_speed, optimal_feed, confidence
            FROM predictions
            WHERE machine_id = $1
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            machine_id,
        )

        if not row:
            raise HTTPException(status_code=404, detail="No predictions found")

        prediction_data = dict(row)
        prediction_data["recommendations"] = []  # Add empty list for recommendations
        return PredictionResponse(**prediction_data)


@app.get("/api/machines/{machine_id}/forecast", response_model=ForecastResponse)
async def get_machine_forecast(
    machine_id: str, start_time: datetime, end_time: datetime, interval: str = "1 hour"
):
    """Get forecast data за машина"""
    cache_key = f"forecast:{machine_id}:{start_time.isoformat()}:{end_time.isoformat()}:{interval}"
    cached_data = await cache_manager.get(cache_key)

    if cached_data:
        return ForecastResponse(**cached_data)

    async with db.pool.acquire() as conn:
        # Validate interval
        valid_intervals = ["15 minutes", "30 minutes", "1 hour", "6 hours", "1 day"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}",
            )

        interval_map = {
            "15 minutes": timedelta(minutes=15),
            "30 minutes": timedelta(minutes=30),
            "1 hour": timedelta(hours=1),
            "6 hours": timedelta(hours=6),
            "1 day": timedelta(days=1),
        }
        interval_timedelta = interval_map.get(interval)

        rows = await conn.fetch(
            f"""
            SELECT
                time_bucket($1, timestamp) AS bucket,
                AVG(anomaly_score) as predicted_anomaly_score,
                AVG(failure_probability) as predicted_failure_probability
                -- Добавете други агрегирани метрики, които да се използват за прогноза
            FROM predictions
            WHERE machine_id = $2
              AND timestamp BETWEEN $3 AND $4
            GROUP BY bucket
            ORDER BY bucket
        """,
            interval_timedelta,
            machine_id,
            start_time,
            end_time,
        )

        forecast_data = []
        for row in rows:
            forecast_data.append(
                ForecastDataPoint(
                    timestamp=row["bucket"],
                    predicted_value=row[
                        "predicted_anomaly_score"
                    ],  # Пример, може да се промени
                )
            )

        response = ForecastResponse(machine_id=machine_id, forecast=forecast_data)
        await cache_manager.set(cache_key, response.dict(), 300)  # 5 minutes
        return response


# ---------- HISTORICAL DATA ----------


@app.post("/api/historical/query")
async def query_historical_data(query: HistoricalQuery):
    """Query исторически данни"""
    async with db.pool.acquire() as conn:
        # Build query
        machine_filter = ""
        if query.machine_ids:
            machine_filter = f"AND machine_id = ANY($3)"

        sql = f"""
            SELECT
                time_bucket('5 minutes', timestamp) AS time,
                machine_id,
                AVG(anomaly_score) as avg_anomaly,
                AVG(failure_probability) as avg_failure_prob,
                MIN(remaining_useful_life) as min_rul,
                AVG(confidence) as avg_confidence
            FROM predictions
            WHERE timestamp BETWEEN $1 AND $2
            {machine_filter}
            GROUP BY time, machine_id
            ORDER BY time DESC
        """

        params = [query.start_time, query.end_time]
        if query.machine_ids:
            params.append(query.machine_ids)

        rows = await conn.fetch(sql, *params)
        return [dict(row) for row in rows]


@app.get("/api/machines/{machine_id}/trends")
async def get_machine_trends(machine_id: str, hours: int = 24):
    """Get trends за последните N часа"""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                time_bucket('1 hour', timestamp) AS hour,
                AVG(anomaly_score) as avg_anomaly,
                MAX(failure_probability) as max_failure_risk,
                MIN(remaining_useful_life) as min_rul,
                AVG(optimal_speed) as avg_optimal_speed,
                COUNT(*) as data_points
            FROM predictions
            WHERE machine_id = $1
              AND timestamp > NOW() - INTERVAL '$2 hours'
            GROUP BY hour, machine_id
            ORDER BY hour DESC
        """,
            machine_id,
            hours,
        )
        return [dict(row) for row in rows]


# ---------- ALERTS ----------


@app.get("/api/alerts", response_model=List[Alert])
async def get_alerts(
    machine_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 100,
):
    """Get alerts с filters"""
    async with db.pool.acquire() as conn:
        # Build query
        filters = []
        params = []
        param_count = 0

        if machine_id:
            param_count += 1
            filters.append(f"machine_id = ${param_count}")
            params.append(machine_id)

        if severity:
            param_count += 1
            filters.append(f"severity = ${param_count}")
            params.append(severity)

        if acknowledged is not None:
            param_count += 1
            filters.append(f"acknowledged = ${param_count}")
            params.append(acknowledged)

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        param_count += 1
        sql = f"""
            SELECT * FROM alerts
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${param_count}
        """
        params.append(limit)

        rows = await conn.fetch(sql, *params)
        return [Alert(**dict(row)) for row in rows]


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, acknowledged_by: str):
    """Acknowledge alert"""
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE alerts
            SET acknowledged = true,
                acknowledged_at = NOW(),
                acknowledged_by = $2
            WHERE id = $1
        """,
            alert_id,
            acknowledged_by,
        )

        return {"status": "acknowledged", "alert_id": alert_id}


# ---------- ANALYTICS & REPORTS ----------


@app.get("/api/analytics/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    """Overall analytics dashboard data"""
    cache_key = "analytics_overview"
    cached_data = await cache_manager.get(cache_key)

    if cached_data:
        return cached_data

    async with db.pool.acquire() as conn:
        # Get stats за последните 24h
        stats = await conn.fetchrow(
            """
            WITH recent_data AS (
                SELECT * FROM predictions
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            )
            SELECT
                COUNT(DISTINCT machine_id) as active_machines,
                AVG(anomaly_score) as avg_anomaly,
                MAX(failure_probability) as max_failure_risk,
                COUNT(CASE WHEN anomaly_score > 0.75 THEN 1 END) as anomalies_detected,
                COUNT(CASE WHEN failure_probability > 0.7 THEN 1 END) as high_risk_machines
            FROM recent_data
        """
        )

        # Get open alerts
        open_alerts = await conn.fetchval(
            """
            SELECT COUNT(*) FROM alerts
            WHERE acknowledged = false
            AND timestamp > NOW() - INTERVAL '7 days'
        """
        )

        # Machine health distribution
        health_dist = await conn.fetch(
            """
            WITH latest_predictions AS (
                SELECT DISTINCT ON (machine_id)
                    machine_id,
                    failure_probability
                FROM predictions
                ORDER BY machine_id, timestamp DESC
            )
            SELECT
                CASE
                    WHEN failure_probability > 0.7 THEN 'critical'
                    WHEN failure_probability > 0.4 THEN 'warning'
                    ELSE 'healthy'
                END as health_status,
                COUNT(*) as count
            FROM latest_predictions
            GROUP BY health_status
        """
        )

        result = {
            "timestamp": datetime.now().isoformat(),
            "active_machines": stats["active_machines"],
            "avg_anomaly_score": float(stats["avg_anomaly"] or 0),
            "max_failure_risk": float(stats["max_failure_risk"] or 0),
            "anomalies_detected_24h": stats["anomalies_detected"],
            "high_risk_machines": stats["high_risk_machines"],
            "open_alerts": open_alerts,
            "health_distribution": {
                row["health_status"]: row["count"] for row in health_dist
            },
        }

        # Cache for 5 minutes
        await cache_manager.set(cache_key, result, 300)
        return result


@app.get("/api/analytics/fleet-efficiency")
async def get_fleet_efficiency():
    """Fleet-wide efficiency metrics"""
    async with db.pool.acquire() as conn:
        efficiency = await conn.fetch(
            """
            SELECT
                machine_id,
                AVG(optimal_speed / NULLIF(optimal_speed, 0)) as speed_efficiency,
                AVG(confidence) as prediction_confidence,
                COUNT(*) as data_points,
                MAX(timestamp) as last_update
            FROM predictions
            WHERE timestamp > NOW() - INTERVAL '6 hours'
            GROUP BY machine_id
            ORDER BY speed_efficiency DESC
        """
        )

        return [dict(row) for row in efficiency]


@app.post("/api/performance/analyze", response_model=PerformanceAnalysisResponse)
async def analyze_machine_performance(request: PerformanceAnalysisRequest):
    """Извършва анализ на производителността на машина за даден период"""
    cache_key = f"performance_analysis:{request.machine_id}:{request.start_time.isoformat()}:{request.end_time.isoformat()}:{request.metrics}"
    cached_data = await cache_manager.get(cache_key)

    if cached_data:
        return PerformanceAnalysisResponse(**cached_data)

    async with db.pool.acquire() as conn:
        # В реална ситуация тук ще има по-сложна логика за извличане и анализ на данни
        # от различни таблици, свързани с производителността на машината.
        # Засега ще използваме таблицата predictions като източник на примерни данни.
        rows = await conn.fetch(
            """
            SELECT
                timestamp,
                anomaly_score as avg_cpu_usage, -- Примерна метрика
                failure_probability as max_temperature, -- Примерна метрика
                optimal_speed as production_rate -- Примерна метрика
            FROM predictions
            WHERE machine_id = $1
              AND timestamp BETWEEN $2 AND $3
            ORDER BY timestamp
        """,
            request.machine_id,
            request.start_time,
            request.end_time,
        )

        analysis_data = []
        for row in rows:
            analysis_data.append(
                PerformanceDataPoint(
                    timestamp=row["timestamp"],
                    avg_cpu_usage=row["avg_cpu_usage"],
                    max_temperature=row["max_temperature"],
                    production_rate=row["production_rate"],
                )
            )

        response = PerformanceAnalysisResponse(
            machine_id=request.machine_id, analysis_data=analysis_data
        )
        await cache_manager.set(cache_key, response.dict(), 300)  # 5 minutes
        return response


# ---------- OPTIMIZATION ----------


@app.post("/api/optimize")
async def request_optimization(request: OptimizationRequest):
    """Request optimization suggestions за машина"""
    # Get последните данни
    async with db.pool.acquire() as conn:
        recent_data = await conn.fetch(
            """
            SELECT * FROM predictions
            WHERE machine_id = $1
            ORDER BY timestamp DESC
            LIMIT 10
        """,
            request.machine_id,
        )

        if not recent_data:
            raise HTTPException(status_code=404, detail="No data for machine")

    # Simple optimization logic (можеш да разшириш с AI)
    avg_failure_prob = sum(r["failure_probability"] for r in recent_data) / len(
        recent_data
    )

    suggestions = []
    if avg_failure_prob > 0.6:
        suggestions.append(
            {
                "type": "maintenance",
                "priority": "high",
                "action": "Schedule preventive maintenance",
                "expected_benefit": "Reduce failure risk by 40%",
            }
        )

    if request.target == "efficiency":
        suggestions.append(
            {
                "type": "parameter",
                "priority": "medium",
                "action": f"Optimize speed to {recent_data[0]['optimal_speed']:.0f} RPM",
                "expected_benefit": "Improve energy efficiency by 15%",
            }
        )

    return {
        "machine_id": request.machine_id,
        "target": request.target,
        "current_status": "critical" if avg_failure_prob > 0.7 else "normal",
        "suggestions": suggestions,
    }


# ---------- CHATBOT ----------


@app.post("/api/chatbot", response_model=ChatbotResponse)
async def chat_with_ai(request: ChatbotRequest):
    """Изпраща съобщение до AI чатбота и връща отговор"""
    request_id = f"chatbot-{request.user_id}-{datetime.now().isoformat()}"

    # Изпращане на заявката към Kafka
    message = {
        "request_id": request_id,
        "user_id": request.user_id,
        "message": request.message,
        "timestamp": datetime.now().isoformat(),
    }

    try:
        db.kafka_producer.send(KafkaConfig.TOPIC_CHATBOT_REQUESTS, message)
        db.kafka_producer.flush()

        # Изчакване на отговор от Redis (ChatbotService ще публикува там)
        response_key = f"chatbot:response:{request_id}"

        # Изчакваме до 30 секунди за отговор
        for _ in range(30):
            response_data = await db.redis.get(response_key)
            if response_data:
                await db.redis.delete(
                    response_key
                )  # Изтриване на отговора след прочитане
                response_json = json.loads(response_data)
                return ChatbotResponse(
                    user_id=response_json["user_id"],
                    response=response_json["response"],
                    timestamp=datetime.fromisoformat(response_json["timestamp"]),
                )
            await asyncio.sleep(1)

        raise HTTPException(status_code=504, detail="Chatbot response timed out")

    except Exception as e:
        logger.error(f"Error in chatbot API: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# ---------- AUTO ML ENDPOINTS ----------


@api_v1.post("/automl/train", response_model=AutoMLTrainingResponse)
async def train_automl_model(
    request: AutoMLTrainingRequest, current_user: User = Depends(get_current_admin_user)
):
    """Train AutoML model on provided dataset."""
    try:
        # Load dataset (simplified - in real implementation, handle file uploads)
        import pandas as pd

        df = pd.read_csv(request.dataset_path)

        # Train AutoML model
        results = await automl_engine.auto_train(
            X=df.drop(columns=[request.target_column]),
            y=df[request.target_column],
            problem_type=request.problem_type,
            test_size=request.test_size,
            cv_folds=request.cv_folds,
        )

        training_response = AutoMLTrainingResponse(
            training_id=f"automl_{int(time.time())}",
            status="completed",
            best_model=results["best_model"],
            best_score=results["best_score"],
            training_time=results["training_time"],
            model_results=results["model_results"],
            feature_importance=results["feature_importance"],
        )

        logger.info(f"AutoML training completed by user {current_user.username}")
        return training_response

    except Exception as e:
        logger.error(f"AutoML training failed: {e}")
        raise HTTPException(status_code=500, detail=f"AutoML training failed: {str(e)}")


@api_v1.post("/automl/train-nas", response_model=AutoMLTrainingResponse)
async def train_automl_with_nas(
    request: AutoMLTrainingRequest, current_user: User = Depends(get_current_admin_user)
):
    """Train AutoML model with Neural Architecture Search."""
    try:
        # Load dataset
        import pandas as pd

        df = pd.read_csv(request.dataset_path)

        # Train AutoML with NAS
        results = await automl_engine.auto_train_with_nas(
            X=df.drop(columns=[request.target_column]),
            y=df[request.target_column],
            problem_type=request.problem_type,
            test_size=request.test_size,
        )

        training_response = AutoMLTrainingResponse(
            training_id=f"automl_nas_{int(time.time())}",
            status="completed",
            best_model=results["best_model"],
            best_score=results["best_score"],
            training_time=results["training_time"],
            model_results=results.get("model_results", {}),
            feature_importance=results.get("feature_importance", {}),
        )

        logger.info(
            f"AutoML with NAS training completed by user {current_user.username}"
        )
        return training_response

    except Exception as e:
        logger.error(f"AutoML with NAS training failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"AutoML with NAS training failed: {str(e)}"
        )


@api_v1.post("/automl/train-multimodal")
async def train_multimodal_model(
    sensor_data_path: str,
    target_column: str,
    text_data_path: Optional[str] = None,
    categorical_columns: Optional[List[str]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Train multi-modal model combining sensor, text, and categorical data."""
    try:
        import pandas as pd

        # Load sensor data
        sensor_df = pd.read_csv(sensor_data_path)

        # Assume target is in sensor data
        targets = sensor_df[target_column]
        sensor_data = sensor_df.drop(columns=[target_column])

        # Load text data if provided
        text_data = None
        if text_data_path:
            text_df = pd.read_csv(text_data_path)
            text_data = text_df.iloc[:, 0].tolist()  # Assume first column is text

        # Extract categorical data
        categorical_data = None
        if categorical_columns:
            categorical_data = {}
            for col in categorical_columns:
                if col in sensor_df.columns:
                    categorical_data[col] = sensor_df[col].tolist()

        # Train multi-modal model
        results = await automl_engine.train_multimodal_model(
            sensor_data=sensor_data,
            text_data=text_data,
            categorical_data=categorical_data,
            targets=targets,
        )

        return {
            "status": "completed",
            "training_id": f"multimodal_{int(time.time())}",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Multi-modal training failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Multi-modal training failed: {str(e)}"
        )


@api_v1.post("/automl/optimize-edge")
async def optimize_model_for_edge(
    calibration_data_path: str,
    target_device: str = "cpu",
    current_user: User = Depends(get_current_admin_user),
):
    """Optimize trained AutoML model for edge deployment."""
    try:
        results = await automl_engine.optimize_model_for_edge_deployment(
            calibration_data_path=calibration_data_path, target_device=target_device
        )

        return {
            "status": "optimized",
            "optimization_id": f"edge_opt_{int(time.time())}",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Edge optimization failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Edge optimization failed: {str(e)}"
        )


@api_v1.get("/automl/models")
async def get_automl_models(current_user: User = Depends(get_current_user)):
    """Get information about trained AutoML models."""
    return automl_engine.get_model_info()


@api_v1.post("/automl/predict")
async def automl_predict(
    data: Dict[str, Any], current_user: User = Depends(get_current_user)
):
    """Make predictions using trained AutoML model."""
    try:
        import pandas as pd

        df = pd.DataFrame([data])
        predictions = automl_engine.predict(df)
        return {"predictions": predictions.tolist()}
    except Exception as e:
        logger.error(f"AutoML prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ---------- REINFORCEMENT LEARNING ENDPOINTS ----------


@api_v1.post("/rl/train", response_model=RLTrainingResponse)
async def train_rl_model(
    request: RLTrainingRequest, current_user: User = Depends(get_current_admin_user)
):
    """Train reinforcement learning model for process optimization."""
    try:
        # Update parameter ranges if provided
        if request.parameter_ranges:
            param_ranges = {
                k: (v[0], v[1]) for k, v in request.parameter_ranges.items()
            }
            global rl_engine
            rl_engine = __import__(
                "reinforcement_learning"
            ).ReinforcementLearningEngine(
                parameter_ranges=param_ranges,
                target_metrics=["efficiency", "quality", "energy_consumption"],
            )

        # Train RL model
        results = await rl_engine.train(
            episodes=request.episodes, max_steps=request.max_steps
        )

        training_response = RLTrainingResponse(
            training_id=f"rl_{int(time.time())}",
            status="completed",
            episodes=results["episodes"],
            training_time=results["training_time"],
            average_reward=results["average_reward"],
            best_reward=results["best_reward"],
            best_parameters=results["best_parameters"],
        )

        logger.info(f"RL training completed by user {current_user.username}")
        return training_response

    except Exception as e:
        logger.error(f"RL training failed: {e}")
        raise HTTPException(status_code=500, detail=f"RL training failed: {str(e)}")


@api_v1.post("/rl/optimize")
async def optimize_parameters(
    current_parameters: Dict[str, float], current_user: User = Depends(get_current_user)
):
    """Optimize process parameters using trained RL model."""
    try:
        optimized = rl_engine.optimize_parameters(current_parameters)
        return {
            "current_parameters": current_parameters,
            "optimized_parameters": optimized,
            "improvements": {
                param: optimized[param] - current_parameters.get(param, 0)
                for param in optimized.keys()
            },
        }
    except Exception as e:
        logger.error(f"RL optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@api_v1.get("/rl/status")
async def get_rl_status(current_user: User = Depends(get_current_user)):
    """Get reinforcement learning model status."""
    return rl_engine.get_training_stats()


# ---------- MULTI-TENANCY ENDPOINTS ----------


@api_v1.post("/tenants")
async def create_tenant(
    tenant_id: str,
    name: str,
    domain: str,
    current_user: User = Depends(get_current_admin_user),
):
    """Create new tenant."""
    try:
        tenant = await tenant_manager.create_tenant(
            tenant_id=tenant_id, name=name, domain=domain, admin_user_id=current_user.id
        )
        return {"status": "created", "tenant": tenant.__dict__}
    except Exception as e:
        logger.error(f"Tenant creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Creation failed: {str(e)}")


@api_v1.get("/tenants")
async def list_tenants(current_user: User = Depends(get_current_admin_user)):
    """List all tenants."""
    try:
        tenants = tenant_manager.list_tenants()
        return {"status": "success", "tenants": tenants}
    except Exception as e:
        logger.error(f"Tenant listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Listing failed: {str(e)}")


@api_v1.get("/tenants/{tenant_id}")
async def get_tenant_details(
    tenant_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Get tenant details."""
    try:
        stats = tenant_manager.get_tenant_stats(tenant_id)
        return {"status": "success", "tenant": stats}
    except Exception as e:
        logger.error(f"Tenant details failed: {e}")
        raise HTTPException(status_code=500, detail=f"Details failed: {str(e)}")


@api_v1.post("/tenants/{tenant_id}/users")
async def add_user_to_tenant(
    tenant_id: str, user_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Add user to tenant."""
    try:
        success = await tenant_manager.add_user_to_tenant(user_id, tenant_id)
        if success:
            return {"status": "added", "user_id": user_id, "tenant_id": tenant_id}
        else:
            raise HTTPException(status_code=404, detail="Tenant or user not found")
    except Exception as e:
        logger.error(f"Add user to tenant failed: {e}")
        raise HTTPException(status_code=500, detail=f"Add failed: {str(e)}")


@api_v1.get("/tenants/{tenant_id}/usage")
async def get_tenant_usage(
    tenant_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Get tenant resource usage."""
    try:
        usage = tenant_manager.resource_usage.get(tenant_id, {})
        return {"status": "success", "usage": usage}
    except Exception as e:
        logger.error(f"Tenant usage retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Usage retrieval failed: {str(e)}")


# ---------- AUDIT LOGGING ENDPOINTS ----------


@api_v1.get("/audit/events")
async def get_audit_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
):
    """Get audit events with filtering."""
    try:
        # Parse dates
        start_time = datetime.fromisoformat(start_date) if start_date else None
        end_time = datetime.fromisoformat(end_date) if end_date else None

        events = await audit_logger.query_events(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            tenant_id=tenant_id,
            event_type=event_type,
            severity=severity,
            limit=limit,
        )

        return {
            "status": "success",
            "events": [event.to_dict() for event in events],
            "count": len(events),
        }
    except Exception as e:
        logger.error(f"Audit events query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@api_v1.post("/audit/compliance-report")
async def generate_compliance_report(
    start_date: str,
    end_date: str,
    report_type: str = "general",
    current_user: User = Depends(get_current_admin_user),
):
    """Generate compliance report."""
    try:
        start_time = datetime.fromisoformat(start_date)
        end_time = datetime.fromisoformat(end_date)

        report = await audit_logger.generate_compliance_report(
            start_date=start_time, end_date=end_time, report_type=report_type
        )

        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"Compliance report generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )


@api_v1.post("/audit/cleanup")
async def cleanup_audit_logs(current_user: User = Depends(get_current_admin_user)):
    """Clean up old audit logs."""
    try:
        cleaned_count = await audit_logger.cleanup_old_logs()
        return {
            "status": "success",
            "message": f"Cleaned up {cleaned_count} old audit events",
        }
    except Exception as e:
        logger.error(f"Audit cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@api_v1.get("/audit/integrity")
async def check_audit_integrity(current_user: User = Depends(get_current_admin_user)):
    """Check audit log integrity."""
    try:
        integrity = await audit_logger.verify_log_integrity()
        return {"status": "success", "integrity": integrity}
    except Exception as e:
        logger.error(f"Integrity check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Integrity check failed: {str(e)}")


# ---------- HEALTH CHECK ----------


# ---------- ENERGY TRADING ENDPOINTS ----------

# Import energy trading modules (lazy import to avoid circular dependencies)
energy_marketplace = None
energy_gui = None


def get_energy_marketplace():
    """Lazy import and get energy marketplace instance."""
    global energy_marketplace
    if energy_marketplace is None:
        try:
#             from src.industry_4_0.energy_trading_marketplace import EnergyTradingMarketplace

            energy_marketplace = EnergyTradingMarketplace()
        except ImportError:
            raise HTTPException(
                status_code=503, detail="Energy trading module not available"
            )
    return energy_marketplace


def get_energy_gui():
    """Lazy import and get energy GUI instance."""
    global energy_gui
    if energy_gui is None:
        try:
#             from src.gui.energy_trading_gui import EnergyTradingGUI

            marketplace = get_energy_marketplace()
            energy_gui = EnergyTradingGUI(marketplace)
        except ImportError:
            raise HTTPException(
                status_code=503, detail="Energy trading GUI not available"
            )
    return energy_gui


@energy_router.get("/")
async def get_energy_trading_dashboard():
    """Get main energy trading dashboard."""
    try:
        gui = get_energy_gui()
        return await gui.get_main_dashboard({})
    except Exception as e:
        logger.error(f"Energy trading dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@energy_router.get("/parks")
async def get_energy_parks_dashboard(park_id: Optional[str] = None):
    """Get energy parks management dashboard."""
    try:
        gui = get_energy_gui()
        request = {"query_params": {"park_id": park_id} if park_id else {}}
        return await gui.get_parks_dashboard(request)
    except Exception as e:
        logger.error(f"Energy parks dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Parks dashboard error: {str(e)}")


@energy_router.get("/market")
async def get_energy_market_dashboard():
    """Get energy trading market dashboard."""
    try:
        gui = get_energy_gui()
        return await gui.get_market_dashboard({})
    except Exception as e:
        logger.error(f"Energy market dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Market dashboard error: {str(e)}")


@energy_router.get("/trades")
async def get_energy_trades_dashboard():
    """Get trades and transactions dashboard."""
    try:
        gui = get_energy_gui()
        return await gui.get_trades_dashboard({})
    except Exception as e:
        logger.error(f"Energy trades dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Trades dashboard error: {str(e)}")


@energy_router.get("/analytics")
async def get_energy_analytics_dashboard():
    """Get analytics and reporting dashboard."""
    try:
        gui = get_energy_gui()
        return await gui.get_analytics_dashboard({})
    except Exception as e:
        logger.error(f"Energy analytics dashboard error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Analytics dashboard error: {str(e)}"
        )


# API endpoints for energy trading
@energy_router.get("/api/market-overview")
async def api_get_market_overview():
    """API endpoint for market overview data."""
    try:
        gui = get_energy_gui()
        return await gui.api_get_market_overview({})
    except Exception as e:
        logger.error(f"Market overview API error: {e}")
        return {"status": "error", "message": str(e)}


@energy_router.get("/api/park-status")
async def api_get_park_status(park_id: str):
    """API endpoint for park status."""
    try:
        gui = get_energy_gui()
        request = {"query_params": {"park_id": park_id}}
        return await gui.api_get_park_status(request)
    except Exception as e:
        logger.error(f"Park status API error: {e}")
        return {"status": "error", "message": str(e)}


@energy_router.post("/api/create-offer")
async def api_create_offer(offer_data: Dict[str, Any]):
    """API endpoint for creating energy offers."""
    try:
        gui = get_energy_gui()
        request = {"body": offer_data}
        return await gui.api_create_offer(request)
    except Exception as e:
        logger.error(f"Create offer API error: {e}")
        return {"status": "error", "message": str(e)}


@energy_router.post("/api/place-bid")
async def api_place_bid(bid_data: Dict[str, Any]):
    """API endpoint for placing bids."""
    try:
        gui = get_energy_gui()
        request = {"body": bid_data}
        return await gui.api_place_bid(request)
    except Exception as e:
        logger.error(f"Place bid API error: {e}")
        return {"status": "error", "message": str(e)}


@energy_router.post("/api/execute-trade")
async def api_execute_trade(trade_data: Dict[str, Any]):
    """API endpoint for executing trades."""
    try:
        gui = get_energy_gui()
        request = {"body": trade_data}
        return await gui.api_execute_trade(request)
    except Exception as e:
        logger.error(f"Execute trade API error: {e}")
        return {"status": "error", "message": str(e)}


# P2P Trading Endpoints


@energy_router.post("/p2p/register-consumer")
async def register_energy_consumer(
    consumer_id: str,
    name: str,
    email: str,
    address: Dict[str, Any],
    devices: Optional[List[Dict[str, Any]]] = None,
    current_user: User = Depends(get_current_user),
):
    """Register a consumer for P2P energy trading."""
    try:
        marketplace = get_energy_marketplace()
        consumer_config = {
            "name": name,
            "email": email,
            "address": address,
            "devices": devices or [],
        }
        result = await marketplace.register_energy_consumer(
            consumer_id, consumer_config
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Consumer registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@energy_router.post("/p2p/create-micro-offer")
async def create_micro_offer(
    seller_id: str,
    energy_amount: float,
    price_per_kwh: float,
    valid_hours: int = 1,
    current_user: User = Depends(get_current_user),
):
    """Create a micro energy offer for P2P trading."""
    try:
        marketplace = get_energy_marketplace()
        offer_config = {
            "energy_amount": energy_amount,
            "price_per_kwh": price_per_kwh,
            "valid_until": time.time() + (valid_hours * 3600),
            "energy_source": "p2p_micro",
        }
        result = await marketplace.create_micro_offer(seller_id, offer_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Micro offer creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Offer creation failed: {str(e)}")


@energy_router.post("/p2p/place-micro-bid")
async def place_micro_bid(
    offer_id: str,
    buyer_id: str,
    energy_amount: float,
    bid_price: float,
    current_user: User = Depends(get_current_user),
):
    """Place a bid on a micro energy offer."""
    try:
        marketplace = get_energy_marketplace()
        bid_config = {"energy_amount": energy_amount, "bid_price": bid_price}
        result = await marketplace.create_micro_bid(offer_id, buyer_id, bid_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Micro bid placement error: {e}")
        raise HTTPException(status_code=500, detail=f"Bid placement failed: {str(e)}")


@energy_router.post("/p2p/execute-micro-trade")
async def execute_micro_trade(
    offer_id: str, bid_id: str, current_user: User = Depends(get_current_user)
):
    """Execute a micro P2P energy trade."""
    try:
        marketplace = get_energy_marketplace()
        result = await marketplace.execute_micro_trade(offer_id, bid_id)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Micro trade execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")


@energy_router.get("/p2p/wallet/{consumer_id}")
async def get_wallet_balance(
    consumer_id: str, current_user: User = Depends(get_current_user)
):
    """Get consumer wallet balance."""
    try:
        marketplace = get_energy_marketplace()
        result = await marketplace.get_wallet_balance(consumer_id)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Wallet balance retrieval error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Balance retrieval failed: {str(e)}"
        )


@energy_router.post("/p2p/wallet/add-funds")
async def add_wallet_funds(
    consumer_id: str,
    amount: float,
    payment_method: str,
    payment_details: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Add funds to consumer wallet."""
    try:
        marketplace = get_energy_marketplace()
        result = await marketplace.add_wallet_funds(
            consumer_id, amount, payment_method, payment_details
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Wallet funding error: {e}")
        raise HTTPException(status_code=500, detail=f"Funding failed: {str(e)}")


@energy_router.post("/p2p/process-payment")
async def process_trade_payment(
    trade_id: str,
    payment_method: str,
    payment_details: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Process payment for an energy trade."""
    try:
        marketplace = get_energy_marketplace()
        result = await marketplace.process_payment(
            trade_id, payment_method, payment_details
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment failed: {str(e)}")


@energy_router.post("/p2p/create-contract")
async def create_energy_contract(
    parties: List[Dict[str, Any]],
    terms: Dict[str, Any],
    conditions: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Create a smart contract for energy trading."""
    try:
        marketplace = get_energy_marketplace()
        contract_config = {
            "parties": parties,
            "terms": terms,
            "conditions": conditions or {},
        }
        result = await marketplace.create_energy_contract(contract_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Contract creation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Contract creation failed: {str(e)}"
        )


@energy_router.post("/p2p/execute-contract/{contract_id}")
async def execute_energy_contract(
    contract_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Execute a smart contract."""
    try:
        marketplace = get_energy_marketplace()
        result = await marketplace.execute_contract(contract_id)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Contract execution error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Contract execution failed: {str(e)}"
        )


# International Markets Endpoints


@energy_router.post("/international/cross-border-offer")
async def create_cross_border_offer(
    seller_id: str,
    buyer_market: str,
    energy_amount: float,
    price_per_kwh: float,
    energy_source: str = "mixed",
    current_user: User = Depends(get_current_user),
):
    """Create a cross-border energy trading offer."""
    try:
        marketplace = get_energy_marketplace()
        offer_config = {
            "energy_amount": energy_amount,
            "price_per_kwh": price_per_kwh,
            "energy_source": energy_source,
            "valid_until": time.time() + (24 * 3600),  # 24 hours
        }
        result = await marketplace.create_cross_border_offer(
            seller_id, buyer_market, offer_config
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Cross-border offer creation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Cross-border offer creation failed: {str(e)}"
        )


@energy_router.get("/international/market-overview")
async def get_international_market_overview():
    """Get international market overview."""
    try:
        marketplace = get_energy_marketplace()
        result = await marketplace.get_market_overview_international()
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"International market overview error: {e}")
        raise HTTPException(status_code=500, detail=f"Market overview failed: {str(e)}")


@energy_router.get("/international/market/{market_code}")
async def get_market_specific_data(market_code: str):
    """Get market-specific data and statistics."""
    try:
        marketplace = get_energy_marketplace()
        result = await marketplace.get_market_specific_data(market_code)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Market data retrieval error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Market data retrieval failed: {str(e)}"
        )


@energy_router.get("/international/locales")
async def get_supported_locales():
    """Get supported locales for localization."""
    try:
        marketplace = get_energy_marketplace()
        locales = marketplace.get_supported_locales()
        return {"status": "success", "locales": locales}
    except Exception as e:
        logger.error(f"Locales retrieval error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Locales retrieval failed: {str(e)}"
        )


@energy_router.get("/international/exchange-rates")
async def get_exchange_rates():
    """Get current exchange rates."""
    try:
        marketplace = get_energy_marketplace()
        rates = marketplace.exchange_rates
        return {"status": "success", "exchange_rates": rates}
    except Exception as e:
        logger.error(f"Exchange rates retrieval error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Exchange rates retrieval failed: {str(e)}"
        )


# AI Trading Agent Endpoints


@energy_router.post("/ai-trading/train")
async def train_ai_trading_models(
    historical_data: List[Dict[str, Any]],
    current_user: User = Depends(get_current_admin_user),
):
    """Train AI trading models."""
    try:
        result = await ai_trading_agent.train_models(historical_data)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"AI training error: {e}")
        raise HTTPException(status_code=500, detail=f"AI training failed: {str(e)}")


@energy_router.post("/ai-trading/predict")
async def get_market_prediction_endpoint(
    market_data: Dict[str, Any], current_user: User = Depends(get_current_user)
):
    """Get market prediction from AI agent."""
    try:
        prediction = await get_market_prediction(market_data)
        return {"status": "success", "prediction": prediction}
    except Exception as e:
        logger.error(f"Market prediction error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Market prediction failed: {str(e)}"
        )


@energy_router.post("/ai-trading/execute")
async def execute_automated_trade_endpoint(
    market_data: Dict[str, Any], current_user: User = Depends(get_current_admin_user)
):
    """Execute automated trade."""
    try:
        trade = await execute_automated_trade(market_data)
        if trade:
            return {"status": "success", "trade": trade}
        else:
            return {"status": "no_action", "message": "No trade executed"}
    except Exception as e:
        logger.error(f"Automated trade execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")


@energy_router.post("/ai-trading/backtest")
async def run_backtest_endpoint(
    historical_data: List[Dict[str, Any]],
    initial_balance: float = 10000.0,
    current_user: User = Depends(get_current_admin_user),
):
    """Run trading strategy backtest."""
    try:
        result = await run_strategy_backtest(historical_data, initial_balance)
        return {"status": "success", "backtest_result": result}
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@energy_router.get("/ai-trading/status")
async def get_trading_agent_status(current_user: User = Depends(get_current_user)):
    """Get AI trading agent status."""
    try:
        status = ai_trading_agent.get_agent_status()
        return {"status": "success", "agent_status": status}
    except Exception as e:
        logger.error(f"Agent status retrieval error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Status retrieval failed: {str(e)}"
        )


@energy_router.post("/ai-trading/create-agent")
async def create_trading_agent_endpoint(
    agent_id: str,
    config: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new AI trading agent."""
    try:
        agent = await create_trading_agent(agent_id, config)
        return {
            "status": "success",
            "agent_id": agent_id,
            "message": "Trading agent created",
        }
    except Exception as e:
        logger.error(f"Trading agent creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent creation failed: {str(e)}")


# Industry-Specific Endpoints

# Pharma Compliance Endpoints


@api_v1.post("/pharma/register-gmp-area")
async def register_gmp_area_endpoint(
    area_id: str,
    name: str,
    compliance_level: str,
    location: Dict[str, Any],
    environmental_controls: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Register GMP area."""
    try:
        area_config = {
            "name": name,
            "compliance_level": compliance_level,
            "location": location,
            "environmental_controls": environmental_controls or {},
        }
        result = await register_gmp_area(area_id, area_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"GMP area registration error: {e}")
        raise HTTPException(
            status_code=500, detail=f"GMP area registration failed: {str(e)}"
        )


@api_v1.post("/pharma/create-batch")
async def create_batch_record_endpoint(
    batch_id: str,
    product_name: str,
    batch_size: float,
    manufacturing_date: str,
    expiry_date: Optional[str] = None,
    gmp_area: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Create batch record."""
    try:
        batch_config = {
            "product_name": product_name,
            "batch_size": batch_size,
            "manufacturing_date": manufacturing_date,
            "expiry_date": expiry_date,
            "gmp_area": gmp_area,
        }
        result = await create_batch_record(batch_id, batch_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Batch creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch creation failed: {str(e)}")


@api_v1.post("/pharma/quality-check")
async def perform_quality_check_endpoint(
    batch_id: str,
    check_type: str,
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Perform quality check."""
    try:
        result = await perform_quality_check(
            batch_id, check_type, parameters, current_user.username
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Quality check error: {e}")
        raise HTTPException(status_code=500, detail=f"Quality check failed: {str(e)}")


@api_v1.post("/pharma/regulatory-report")
async def generate_regulatory_report_endpoint(
    report_type: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_admin_user),
):
    """Generate regulatory report."""
    try:
        result = await generate_regulatory_report(report_type, start_date, end_date)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Regulatory report error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Regulatory report failed: {str(e)}"
        )


# Chemical Process Safety Endpoints


@api_v1.post("/chemical/register-unit")
async def register_process_unit_endpoint(
    unit_id: str,
    name: str,
    chemicals_handled: List[Dict[str, Any]],
    operating_conditions: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Register process unit."""
    try:
        unit_config = {
            "name": name,
            "chemicals_handled": chemicals_handled,
            "operating_conditions": operating_conditions or {},
        }
        result = await register_process_unit(unit_id, unit_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Process unit registration error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Process unit registration failed: {str(e)}"
        )


@api_v1.post("/chemical/hazop-study")
async def perform_hazop_study_endpoint(
    unit_id: str,
    team_members: List[str],
    current_user: User = Depends(get_current_admin_user),
):
    """Perform HAZOP study."""
    try:
        study_config = {"team_members": team_members}
        result = await perform_hazop_study(unit_id, study_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"HAZOP study error: {e}")
        raise HTTPException(status_code=500, detail=f"HAZOP study failed: {str(e)}")


@api_v1.post("/chemical/sil-assessment")
async def perform_sil_assessment_endpoint(
    unit_id: str,
    function_name: str,
    consequence_severity: int,
    likelihood_frequency: int,
    current_user: User = Depends(get_current_admin_user),
):
    """Perform SIL assessment."""
    try:
        function_config = {
            "function_name": function_name,
            "consequence_severity": consequence_severity,
            "likelihood_frequency": likelihood_frequency,
            "assessor": current_user.username,
        }
        result = await perform_sil_assessment(unit_id, function_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"SIL assessment error: {e}")
        raise HTTPException(status_code=500, detail=f"SIL assessment failed: {str(e)}")


@api_v1.post("/chemical/report-incident")
async def report_safety_incident_endpoint(
    title: str,
    description: str,
    severity: str,
    unit_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Report safety incident."""
    try:
        incident_config = {
            "title": title,
            "description": description,
            "severity": severity,
            "unit_id": unit_id,
            "reported_by": current_user.username,
        }
        result = await report_safety_incident(incident_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Safety incident report error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Safety incident report failed: {str(e)}"
        )


@api_v1.post("/chemical/safety-report")
async def generate_safety_report_endpoint(
    report_type: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_admin_user),
):
    """Generate safety report."""
    try:
        result = await generate_safety_report(report_type, start_date, end_date)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Safety report error: {e}")
        raise HTTPException(status_code=500, detail=f"Safety report failed: {str(e)}")


# Automotive Quality Control Endpoints


@api_v1.post("/automotive/register-product")
async def register_product_endpoint(
    product_id: str,
    name: str,
    customer: str,
    specifications: Dict[str, Any],
    critical_characteristics: Optional[List[Dict[str, Any]]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Register automotive product."""
    try:
        product_config = {
            "name": name,
            "customer": customer,
            "specifications": specifications,
            "critical_characteristics": critical_characteristics or [],
        }
        result = await register_product(product_id, product_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Product registration error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Product registration failed: {str(e)}"
        )


@api_v1.post("/automotive/create-apqp")
async def create_apqp_project_endpoint(
    project_id: str,
    product_id: str,
    title: str,
    team_members: List[str],
    target_completion: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Create APQP project."""
    try:
        project_config = {
            "product_id": product_id,
            "title": title,
            "team_members": team_members,
            "target_completion": target_completion,
        }
        result = await create_apqp_project(project_id, project_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"APQP project creation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"APQP project creation failed: {str(e)}"
        )


@api_v1.post("/automotive/submit-ppap")
async def submit_ppap_endpoint(
    submission_id: str,
    product_id: str,
    submission_level: str = "Level 3",
    current_user: User = Depends(get_current_user),
):
    """Submit PPAP."""
    try:
        submission_config = {
            "product_id": product_id,
            "submission_level": submission_level,
            "submitted_by": current_user.username,
        }
        result = await submit_ppap(submission_id, submission_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"PPAP submission error: {e}")
        raise HTTPException(status_code=500, detail=f"PPAP submission failed: {str(e)}")


@api_v1.post("/automotive/update-spc")
async def update_spc_data_endpoint(
    chart_id: str,
    value: float,
    batch_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Update SPC data."""
    try:
        measurement_data = {
            "value": value,
            "batch_id": batch_id,
            "operator": current_user.username,
        }
        result = await update_spc_data(chart_id, measurement_data)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"SPC update error: {e}")
        raise HTTPException(status_code=500, detail=f"SPC update failed: {str(e)}")


@api_v1.post("/automotive/report-nc")
async def report_non_conformance_endpoint(
    description: str,
    severity: str,
    product_id: Optional[str] = None,
    quantity_affected: int = 1,
    current_user: User = Depends(get_current_user),
):
    """Report non-conformance."""
    try:
        nc_config = {
            "description": description,
            "severity": severity,
            "product_id": product_id,
            "quantity_affected": quantity_affected,
            "reported_by": current_user.username,
        }
        result = await report_non_conformance(nc_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Non-conformance report error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Non-conformance report failed: {str(e)}"
        )


@api_v1.post("/automotive/quality-report")
async def generate_quality_report_endpoint(
    report_type: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_admin_user),
):
    """Generate quality report."""
    try:
        result = await generate_quality_report(report_type, start_date, end_date)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Quality report error: {e}")
        raise HTTPException(status_code=500, detail=f"Quality report failed: {str(e)}")


# Partnerships Integration Endpoints


@api_v1.post("/partnerships/register")
async def register_partner_endpoint(
    partner_id: str,
    name: str,
    partner_type: str,
    api_endpoints: Dict[str, Any],
    authentication: Dict[str, Any],
    capabilities: Optional[List[str]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Register a strategic partner."""
    try:
        partner_config = {
            "name": name,
            "type": partner_type,
            "api_endpoints": api_endpoints,
            "authentication": authentication,
            "capabilities": capabilities or [],
        }
        result = await register_partner(partner_id, partner_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Partner registration error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Partner registration failed: {str(e)}"
        )


@api_v1.post("/partnerships/{partner_id}/sync")
async def sync_partner_data_endpoint(
    partner_id: str,
    data_types: List[str],
    sync_config: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Sync data with partner."""
    try:
        result = await sync_partner_data(partner_id, data_types, sync_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Partner data sync error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Partner data sync failed: {str(e)}"
        )


@api_v1.get("/partnerships/{partner_id}/analytics")
async def get_partner_analytics_endpoint(
    partner_id: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
):
    """Get partner analytics."""
    try:
        result = await get_partner_analytics(partner_id, start_date, end_date)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Partner analytics error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Partner analytics failed: {str(e)}"
        )


@api_v1.get("/partnerships/{partner_id}/status")
async def get_partner_status_endpoint(partner_id: str):
    """Get partner integration status."""
    try:
        status = partnerships_integration.get_partner_status(partner_id)
        if status:
            return {"status": "success", "data": status}
        else:
            raise HTTPException(
                status_code=404, detail=f"Partner {partner_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Partner status error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Partner status retrieval failed: {str(e)}"
        )


@api_v1.get("/partnerships/logs")
async def get_integration_logs_endpoint(
    partner_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """Get integration activity logs."""
    try:
        logs = partnerships_integration.get_integration_logs(partner_id, limit)
        return {"status": "success", "logs": logs}
    except Exception as e:
        logger.error(f"Integration logs error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Integration logs retrieval failed: {str(e)}"
        )


@api_v1.post("/partnerships/mappings/create")
async def create_data_mapping_endpoint(
    mapping_id: str,
    source_partner: str,
    target_system: str,
    field_mappings: List[Dict[str, Any]],
    transformations: Optional[List[Dict[str, Any]]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Create data mapping."""
    try:
        mapping_config = {
            "field_mappings": field_mappings,
            "transformations": transformations or [],
        }
        result = await create_data_mapping(
            mapping_id, source_partner, target_system, mapping_config
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Data mapping creation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Data mapping creation failed: {str(e)}"
        )


@api_v1.post("/partnerships/mappings/{mapping_id}/execute")
async def execute_data_mapping_endpoint(
    mapping_id: str,
    source_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Execute data mapping."""
    try:
        result = await execute_data_mapping(mapping_id, source_data)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Data mapping execution error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Data mapping execution failed: {str(e)}"
        )


# Sales and Channel Management Endpoints


@api_v1.post("/sales/register-rep")
async def register_sales_rep_endpoint(
    rep_id: str,
    name: str,
    email: str,
    role: str = "sales_rep",
    region: str = "EMEA",
    territory: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Register sales representative."""
    try:
        rep_config = {
            "name": name,
            "email": email,
            "role": role,
            "region": region,
            "territory": territory,
        }
        result = await register_sales_rep(rep_id, rep_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Sales rep registration error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sales rep registration failed: {str(e)}"
        )


@api_v1.post("/sales/create-territory")
async def create_territory_endpoint(
    territory_id: str,
    name: str,
    region: str,
    countries: List[str],
    market_size: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Create sales territory."""
    try:
        territory_config = {
            "name": name,
            "region": region,
            "countries": countries,
            "market_size": market_size,
        }
        result = await create_territory(territory_id, territory_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Territory creation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Territory creation failed: {str(e)}"
        )


@api_v1.post("/sales/register-partner")
async def register_channel_partner_endpoint(
    partner_id: str,
    name: str,
    partner_type: str = "partner_reseller",
    tier: str = "bronze",
    territory: Optional[str] = None,
    specializations: Optional[List[str]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Register channel partner."""
    try:
        partner_config = {
            "name": name,
            "type": partner_type,
            "tier": tier,
            "territory": territory,
            "specializations": specializations or [],
        }
        result = await register_channel_partner(partner_id, partner_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Channel partner registration error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Channel partner registration failed: {str(e)}"
        )


@api_v1.post("/sales/register-customer")
async def register_customer_endpoint(
    customer_id: str,
    name: str,
    segment: str = "enterprise",
    industry: Optional[str] = None,
    location: Optional[Dict[str, Any]] = None,
    assigned_rep: Optional[str] = None,
    channel_partner: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Register customer."""
    try:
        customer_config = {
            "name": name,
            "segment": segment,
            "industry": industry,
            "location": location,
            "assigned_rep": assigned_rep,
            "channel_partner": channel_partner,
        }
        result = await register_customer(customer_id, customer_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Customer registration error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Customer registration failed: {str(e)}"
        )


@api_v1.post("/sales/create-opportunity")
async def create_sales_opportunity_endpoint(
    opportunity_id: str,
    customer_id: str,
    estimated_value: float,
    probability: float = 0.5,
    assigned_rep: Optional[str] = None,
    channel_partner: Optional[str] = None,
    product_interest: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
):
    """Create sales opportunity."""
    try:
        opportunity_config = {
            "customer_id": customer_id,
            "estimated_value": estimated_value,
            "probability": probability,
            "assigned_rep": assigned_rep,
            "channel_partner": channel_partner,
            "product_interest": product_interest or [],
        }
        result = await create_sales_opportunity(opportunity_id, opportunity_config)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Sales opportunity creation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sales opportunity creation failed: {str(e)}"
        )


@api_v1.post("/sales/generate-forecast")
async def generate_sales_forecast_endpoint(
    forecast_period: str = "3_months",
    current_user: User = Depends(get_current_admin_user),
):
    """Generate sales forecast."""
    try:
        result = await generate_sales_forecast(forecast_period)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Sales forecast generation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sales forecast generation failed: {str(e)}"
        )


@api_v1.get("/sales/analytics")
async def get_sales_analytics_endpoint(
    start_date: str,
    end_date: str,
    group_by: str = "month",
    current_user: User = Depends(get_current_admin_user),
):
    """Get sales analytics."""
    try:
        result = await get_sales_analytics(start_date, end_date, group_by)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Sales analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Sales analytics failed: {str(e)}")


@api_v1.get("/sales/rep/{rep_id}/status")
async def get_sales_rep_status_endpoint(rep_id: str):
    """Get sales rep status."""
    try:
        status = sales_channel_management.get_sales_rep_status(rep_id)
        if status:
            return {"status": "success", "data": status}
        else:
            raise HTTPException(status_code=404, detail=f"Sales rep {rep_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sales rep status error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sales rep status retrieval failed: {str(e)}"
        )


@api_v1.get("/sales/partner/{partner_id}/status")
async def get_channel_partner_status_endpoint(partner_id: str):
    """Get channel partner status."""
    try:
        status = sales_channel_management.get_partner_status(partner_id)
        if status:
            return {"status": "success", "data": status}
        else:
            raise HTTPException(
                status_code=404, detail=f"Channel partner {partner_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Channel partner status error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Channel partner status retrieval failed: {str(e)}"
        )


# ---------- HEALTH CHECK ----------


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check DB
    try:
        async with db.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    # Check Redis
    try:
        await db.redis.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"

    return {
        "status": "healthy"
        if db_status == "healthy" and redis_status == "healthy"
        else "degraded",
        "components": {
            "database": db_status,
            "redis": redis_status,
            "websocket": "healthy"
            if ws_manager.active_connections
            else "no_connections",
        },
        "active_connections": len(ws_manager.active_connections),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint."""
    from fastapi.responses import Response

    health_status = performance_monitor.get_health_status()

    metrics_lines = []

    # System metrics
    system_metrics = health_status["system_metrics"]
    metrics_lines.append("# HELP cpu_usage_percent Current CPU usage percentage")
    metrics_lines.append("# TYPE cpu_usage_percent gauge")
    metrics_lines.append(f'cpu_usage_percent {system_metrics["cpu_percent"]}')

    metrics_lines.append("# HELP memory_usage_percent Current memory usage percentage")
    metrics_lines.append("# TYPE memory_usage_percent gauge")
    metrics_lines.append(f'memory_usage_percent {system_metrics["memory_percent"]}')

    # Performance metrics
    for operation, metrics in health_status["performance_summary"].items():
        safe_name = operation.replace("/", "_").replace("-", "_")
        metrics_lines.append(
            f"# HELP {safe_name}_requests_total Total requests for {operation}"
        )
        metrics_lines.append(f"# TYPE {safe_name}_requests_total counter")
        metrics_lines.append(f'{safe_name}_requests_total {metrics["total_count"]}')

        metrics_lines.append(
            f"# HELP {safe_name}_error_rate Error rate for {operation}"
        )
        metrics_lines.append(f"# TYPE {safe_name}_error_rate gauge")
        metrics_lines.append(f'{safe_name}_error_rate {metrics["error_rate"]}')

        metrics_lines.append(
            f"# HELP {safe_name}_response_time_p95 P95 response time for {operation}"
        )
        metrics_lines.append(f"# TYPE {safe_name}_response_time_p95 gauge")
        metrics_lines.append(
            f'{safe_name}_response_time_p95 {metrics["p95_duration_ms"]}'
        )

    # API status
    status_value = 1 if health_status["overall_status"] == "healthy" else 0
    metrics_lines.append(
        "# HELP api_health_status API health status (1=healthy, 0=unhealthy)"
    )
    metrics_lines.append("# TYPE api_health_status gauge")
    metrics_lines.append(f"api_health_status {status_value}")

    return Response(
        content="\n".join(metrics_lines),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# ---------- SECURITY AUDIT ENDPOINTS ----------


@api_v1.post("/security/audit")
async def run_security_audit_endpoint(
    target_url: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Run security audit."""
    try:
        url = target_url or "http://localhost:8000"
        results = await run_security_audit(url)
        return {"status": "completed", "results": results}
    except Exception as e:
        logger.error(f"Security audit failed: {e}")
        raise HTTPException(status_code=500, detail=f"Security audit failed: {str(e)}")


@api_v1.get("/security/hardening-plan")
async def get_hardening_plan(current_user: User = Depends(get_current_admin_user)):
    """Get security hardening plan."""
    try:
        plan = generate_hardening_plan()
        return {"status": "generated", "plan": plan}
    except Exception as e:
        logger.error(f"Hardening plan generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Hardening plan generation failed: {str(e)}"
        )


# ---------- DATABASE OPTIMIZATION ENDPOINTS ----------


@api_v1.post("/db/optimize")
async def optimize_database(current_user: User = Depends(get_current_admin_user)):
    """Run database optimization."""
    try:
        result = await db.optimizer.optimize_queries()
        return {"status": "optimization_completed", "result": result}
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Database optimization failed: {str(e)}"
        )


@api_v1.post("/db/create-indexes")
async def create_performance_indexes(
    current_user: User = Depends(get_current_admin_user),
):
    """Create performance indexes."""
    try:
        result = await db.optimizer.create_performance_indexes()
        return {"status": "indexes_created", "result": result}
    except Exception as e:
        logger.error(f"Index creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Index creation failed: {str(e)}")


@api_v1.get("/db/performance")
async def get_database_performance(
    current_user: User = Depends(get_current_admin_user),
):
    """Get database performance metrics."""
    try:
        result = await db.optimizer.monitor_performance()
        return {"status": "metrics_retrieved", "metrics": result}
    except Exception as e:
        logger.error(f"Performance monitoring failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Performance monitoring failed: {str(e)}"
        )


@api_v1.get("/db/optimization-report")
async def get_optimization_report(current_user: User = Depends(get_current_admin_user)):
    """Get database optimization report."""
    try:
        result = db.optimizer.get_optimization_report()
        return {"status": "report_generated", "report": result}
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )


# ---------- ROOT CAUSE ANALYSIS ENDPOINTS ----------


@api_v1.post("/rca/analyze")
async def analyze_root_cause_endpoint(
    incident_data: Dict[str, Any],
    sensor_data_path: str,
    log_data_path: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Perform root cause analysis for an incident."""
    try:
        results = await analyze_root_cause(
            incident_data=incident_data,
            sensor_data_path=sensor_data_path,
            log_data_path=log_data_path,
        )
        return {"status": "analysis_completed", "results": results}
    except Exception as e:
        logger.error(f"Root cause analysis failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Root cause analysis failed: {str(e)}"
        )


@api_v1.get("/rca/history")
async def get_rca_history(
    limit: int = 10, current_user: User = Depends(get_current_admin_user)
):
    """Get root cause analysis history."""
    try:
        history = root_cause_engine.get_analysis_history(limit)
        return {"status": "history_retrieved", "history": history}
    except Exception as e:
        logger.error(f"Failed to get RCA history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get RCA history: {str(e)}"
        )


# ---------- FEDERATED LEARNING ENDPOINTS ----------

federated_orchestrator = FederatedLearningOrchestrator()


class FederatedParticipantRequest(BaseModel):
    participant_id: str
    metadata: Dict[str, Any]


class FederatedTaskRequest(BaseModel):
    task_id: str
    model_configuration: Dict[str, Any]
    dataset_config: Dict[str, Any]
    participants: List[str]


@api_v1.post("/federated/register-participant")
async def register_federated_participant(
    request: FederatedParticipantRequest,
    current_user: User = Depends(get_current_admin_user),
):
    """Register a new participant in federated learning network."""
    try:
        token = await federated_orchestrator.register_participant(
            request.participant_id, request.metadata
        )
        return {
            "status": "registered",
            "participant_id": request.participant_id,
            "token": token,
        }
    except Exception as e:
        logger.error(f"Failed to register participant: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@api_v1.post("/federated/create-task")
async def create_federated_task(
    request: FederatedTaskRequest,
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new federated learning task."""
    try:
        task_config = await federated_orchestrator.create_learning_task(
            request.task_id, request.model_configuration, request.dataset_config, request.participants
        )
        return {"status": "created", "task": task_config}
    except Exception as e:
        logger.error(f"Failed to create federated task: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")


@api_v1.post("/federated/start-round")
async def start_federated_round(
    task_id: str,
    global_model_weights: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_admin_user),
):
    """Start a new training round for federated learning."""
    try:
        round_config = await federated_orchestrator.start_training_round(
            task_id, global_model_weights
        )
        return {"status": "started", "round": round_config}
    except Exception as e:
        logger.error(f"Failed to start federated round: {e}")
        raise HTTPException(status_code=500, detail=f"Round start failed: {str(e)}")


@api_v1.post("/federated/submit-update")
async def submit_model_update(
    task_id: str,
    participant_id: str,
    model_update: Dict[str, Any],
    metadata: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user),
):
    """Submit model update from participant."""
    try:
        accepted = await federated_orchestrator.submit_model_update(
            task_id, participant_id, model_update, metadata
        )
        return {"status": "submitted" if accepted else "rejected", "accepted": accepted}
    except Exception as e:
        logger.error(f"Failed to submit model update: {e}")
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")


@api_v1.get("/federated/task/{task_id}")
async def get_federated_task_status(
    task_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Get status of federated learning task."""
    try:
        status = await federated_orchestrator.get_task_status(task_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "retrieved", "task": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Status retrieval failed: {str(e)}"
        )


@api_v1.get("/federated/participant/{participant_id}")
async def get_participant_stats(
    participant_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Get statistics for a federated learning participant."""
    try:
        stats = await federated_orchestrator.get_participant_stats(participant_id)
        if stats is None:
            raise HTTPException(status_code=404, detail="Participant not found")
        return {"status": "retrieved", "participant": stats}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get participant stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@api_v1.get("/federated/model/{task_id}")
async def get_global_model(
    task_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Get the global model for a completed federated task."""
    try:
        model = federated_orchestrator.get_global_model(task_id)
        if model is None:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"status": "retrieved", "model": model}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get global model: {e}")
        raise HTTPException(status_code=500, detail=f"Model retrieval failed: {str(e)}")


# ============================================================================
# GENERIC MODULE ENDPOINTS
# ============================================================================

@app.get("/modules/{module_id}", response_class=HTMLResponse)
async def get_module_gui(module_id: str, current_user: User = Depends(get_current_user)):
    """Serve a generic module GUI."""
    try:
        template_path = Path(__file__).parent.parent / "templates" / "generic_module_gui.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        else:
            return HTMLResponse(
                content="<h1>Module GUI</h1><p>Template not found</p>",
                status_code=404,
            )

        # Get module info
        module_info = await get_module_info(module_id)

        # Replace template variables
        content = template_content
        content = content.replace("{{ module_id }}", module_id)
        content = content.replace("{{ module_name }}", module_info.get("name", module_id))
        content = content.replace("{{ module_description }}", module_info.get("description", ""))
        content = content.replace("{{ module_icon }}", module_info.get("icon", "fas fa-cogs"))
        content = content.replace("{{ module_status }}", module_info.get("status", "unknown"))

        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Failed to serve module GUI for {module_id}: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


async def get_module_info(module_id: str):
    """Get module information."""
    # Mock module info - in real implementation, this would come from a database
    module_info_map = {
        "energy_monitoring_dashboard": {
            "name": "Energy Monitoring Dashboard",
            "description": "Real-time energy consumption monitoring and optimization insights",
            "icon": "fas fa-bolt",
            "status": "healthy"
        },
        "data_quality_governance": {
            "name": "Data Quality & Schema Governance",
            "description": "Automated data validation, schema management, and quality monitoring",
            "icon": "fas fa-database",
            "status": "healthy"
        },
        "model_drift_monitoring": {
            "name": "Model Drift Monitoring",
            "description": "Continuous monitoring of AI model performance and drift detection",
            "icon": "fas fa-chart-line",
            "status": "healthy"
        },
        "centralized_feature_store": {
            "name": "Centralized Feature Store",
            "description": "Feature engineering, storage, and management for ML pipelines",
            "icon": "fas fa-store",
            "status": "healthy"
        },
        "explainable_ai_engine": {
            "name": "Explainable AI Engine",
            "description": "SHAP and LIME explanations for AI model decisions",
            "icon": "fas fa-search",
            "status": "healthy"
        },
        "simulation_digital_twin": {
            "name": "Simulation & Digital Twin",
            "description": "Digital twin creation and simulation for predictive maintenance",
            "icon": "fas fa-cube",
            "status": "healthy"
        },
        "real_time_optimization": {
            "name": "Real-Time Optimization (RL)",
            "description": "Reinforcement learning for real-time process optimization",
            "icon": "fas fa-rocket",
            "status": "healthy"
        },
        "automated_mlops_pipeline": {
            "name": "Automated MLOps Pipeline",
            "description": "End-to-end ML pipeline management and deployment",
            "icon": "fas fa-cogs",
            "status": "healthy"
        },
        "data_lineage_audit": {
            "name": "Data Lineage & Audit Trail",
            "description": "Complete data flow tracking and audit logging",
            "icon": "fas fa-route",
            "status": "healthy"
        },
        "multi_tenancy_access_control": {
            "name": "Multi-Tenancy & Access Control",
            "description": "Tenant isolation and role-based access management",
            "icon": "fas fa-users",
            "status": "healthy"
        },
        "edge_ai_inference_gateway": {
            "name": "Edge AI Inference Gateway",
            "description": "Edge computing and AI inference management",
            "icon": "fas fa-network-wired",
            "status": "healthy"
        },
        "predictive_quality_control": {
            "name": "Predictive Quality Control",
            "description": "AI-driven quality prediction and defect prevention",
            "icon": "fas fa-check-double",
            "status": "healthy"
        },
        "supply_chain_inventory_predictor": {
            "name": "Supply Chain & Inventory Predictor",
            "description": "Predictive analytics for supply chain and inventory management",
            "icon": "fas fa-boxes",
            "status": "healthy"
        },
        "event_replay_engine": {
            "name": "Event Replay Engine",
            "description": "Historical event replay for testing and analysis",
            "icon": "fas fa-history",
            "status": "healthy"
        },
        "graphql_query_service": {
            "name": "GraphQL Query Service",
            "description": "Flexible data querying with GraphQL API",
            "icon": "fas fa-code",
            "status": "healthy"
        },
        "kpi_benchmarking_engine": {
            "name": "KPI Benchmarking Engine",
            "description": "Performance benchmarking and KPI comparison",
            "icon": "fas fa-trophy",
            "status": "healthy"
        },
        "collaborative_labeling_tool": {
            "name": "Collaborative Labeling Tool",
            "description": "Human-in-the-loop data labeling and validation",
            "icon": "fas fa-users-cog",
            "status": "healthy"
        },
        "root_cause_analysis_engine": {
            "name": "Root Cause Analysis Engine",
            "description": "Automated root cause analysis for incidents",
            "icon": "fas fa-search-plus",
            "status": "healthy"
        },
        "notification_intelligence": {
            "name": "Notification Intelligence",
            "description": "Smart alerting and notification management",
            "icon": "fas fa-bell",
            "status": "healthy"
        },
        "automated_configuration_optimizer": {
            "name": "Automated Configuration Optimizer",
            "description": "AI-driven system configuration optimization",
            "icon": "fas fa-sliders-h",
            "status": "healthy"
        },
        "federated_learning_orchestrator": {
            "name": "Federated Learning Orchestrator",
            "description": "Privacy-preserving distributed machine learning",
            "icon": "fas fa-share-alt",
            "status": "healthy"
        },
        "contextual_anomaly_classifier": {
            "name": "Contextual Anomaly Classifier",
            "description": "Context-aware anomaly detection and classification",
            "icon": "fas fa-exclamation-triangle",
            "status": "healthy"
        },
        "predictive_scheduling_engine": {
            "name": "Predictive Scheduling Engine",
            "description": "AI-powered production and maintenance scheduling",
            "icon": "fas fa-calendar-alt",
            "status": "healthy"
        },
        "enduser_usage_dashboard": {
            "name": "Enduser Usage Dashboard",
            "description": "User activity and platform usage analytics",
            "icon": "fas fa-user-friends",
            "status": "healthy"
        },
        "multi_tenant_kpi_segregation": {
            "name": "Multi-Tenant KPI Segregation",
            "description": "Tenant-specific KPI management and reporting",
            "icon": "fas fa-building",
            "status": "healthy"
        },
        "multi_tenant_resource_management": {
            "name": "Multi-Tenant Resource Management",
            "description": "Resource allocation and management across tenants",
            "icon": "fas fa-server",
            "status": "healthy"
        },
        "auto_mlworkflow_optimization_engine": {
            "name": "Auto MLWorkflow Optimization Engine",
            "description": "Automated ML workflow optimization and tuning",
            "icon": "fas fa-magic",
            "status": "healthy"
        },
        "ai_build_prompt_aggregation_routing": {
            "name": "AI Build Prompt Aggregation & Routing",
            "description": "AI prompt management and intelligent routing",
            "icon": "fas fa-route",
            "status": "healthy"
        },
        "fleet_management_manager": {
            "name": "Fleet Management Manager",
            "description": "Comprehensive fleet asset management and monitoring",
            "icon": "fas fa-truck",
            "status": "healthy"
        },
        "custom_ota_builder": {
            "name": "Custom OTA Builder",
            "description": "Over-the-air update creation and deployment",
            "icon": "fas fa-cloud-upload-alt",
            "status": "healthy"
        },
        "custom_heartbeats_notifications": {
            "name": "Custom Heartbeats Notifications",
            "description": "Customizable heartbeat monitoring and alerts",
            "icon": "fas fa-heartbeat",
            "status": "healthy"
        },
        "marketplace_flux_factor": {
            "name": "Marketplace Flux Factor",
            "description": "Dynamic marketplace pricing and flux calculations",
            "icon": "fas fa-calculator",
            "status": "healthy"
        },
        "issue_tracking_tool": {
            "name": "Issue Tracking Tool",
            "description": "Comprehensive issue tracking and management system",
            "icon": "fas fa-tasks",
            "status": "healthy"
        },
        "object_anatomy_ai": {
            "name": "Object Anatomy AI",
            "description": "AI-powered object analysis and anatomy breakdown",
            "icon": "fas fa-microscope",
            "status": "healthy"
        },
        "daily_progression_notifications": {
            "name": "Daily Progression Notifications",
            "description": "AI-driven progress tracking and notifications",
            "icon": "fas fa-chart-bar",
            "status": "healthy"
        }
    }

    return module_info_map.get(module_id, {
        "name": module_id.replace("_", " ").title(),
        "description": f"Module for {module_id}",
        "icon": "fas fa-cogs",
        "status": "unknown"
    })


@api_v1.get("/modules/{module_id}/metrics")
async def get_module_metrics(module_id: str, range: str = "24h", current_user: User = Depends(get_current_user)):
    """Get module metrics."""
    try:
        # Mock metrics based on module type
        if "energy" in module_id:
            return [
                {"label": "Total Consumption", "value": "1,245 kWh", "trend": 2.3},
                {"label": "Peak Demand", "value": "89 kW", "trend": -1.5},
                {"label": "Efficiency", "value": "87%", "trend": 5.1},
                {"label": "Cost Savings", "value": "€1,250", "trend": 12.4}
            ]
        elif "ai" in module_id or "ml" in module_id:
            return [
                {"label": "Model Accuracy", "value": "94.2%", "trend": 1.8},
                {"label": "Predictions/Hour", "value": "2,450", "trend": 8.7},
                {"label": "Training Time", "value": "45 min", "trend": -15.3},
                {"label": "Data Processed", "value": "1.2 GB", "trend": 22.1}
            ]
        elif "data" in module_id:
            return [
                {"label": "Data Quality Score", "value": "96%", "trend": 3.2},
                {"label": "Records Processed", "value": "45,231", "trend": 12.5},
                {"label": "Schema Violations", "value": "12", "trend": -25.0},
                {"label": "Storage Used", "value": "2.3 TB", "trend": 5.8}
            ]
        else:
            return [
                {"label": "Active Instances", "value": "24", "trend": 4.2},
                {"label": "Success Rate", "value": "98.5%", "trend": 0.8},
                {"label": "Response Time", "value": "145 ms", "trend": -2.1},
                {"label": "Uptime", "value": "99.9%", "trend": 0.1}
            ]
    except Exception as e:
        logger.error(f"Error getting metrics for {module_id}: {e}")
        return []


@api_v1.get("/modules/{module_id}/chart-data")
async def get_module_chart_data(module_id: str, range: str = "24h", current_user: User = Depends(get_current_user)):
    """Get module chart data."""
    try:
        # Generate mock chart data
        import random
        from datetime import datetime, timedelta

        now = datetime.now()
        data_points = 24 if range == "24h" else 7 if range == "7d" else 6

        # Primary chart data
        primary_labels = []
        primary_values = []
        for i in range(data_points):
            timestamp = now - timedelta(hours=data_points-i-1)
            primary_labels.append(timestamp.isoformat())
            primary_values.append(random.randint(50, 150))

        # Distribution data
        distribution_labels = ["Category A", "Category B", "Category C", "Category D", "Category E"]
        distribution_values = [random.randint(10, 50) for _ in range(5)]

        # Trend data
        trend_labels = [f"Period {i+1}" for i in range(data_points)]
        trend_values = []
        base = 100
        for _ in range(data_points):
            base += random.randint(-10, 15)
            trend_values.append(base)

        return {
            "primary": {
                "labels": primary_labels,
                "values": primary_values
            },
            "distribution": {
                "labels": distribution_labels,
                "values": distribution_values
            },
            "trend": {
                "labels": trend_labels,
                "values": trend_values
            }
        }
    except Exception as e:
        logger.error(f"Error getting chart data for {module_id}: {e}")
        return {"primary": {"labels": [], "values": []}, "distribution": {"labels": [], "values": []}, "trend": {"labels": [], "values": []}}


@api_v1.get("/modules/{module_id}/table-data")
async def get_module_table_data(module_id: str, range: str = "24h", current_user: User = Depends(get_current_user)):
    """Get module table data."""
    try:
        # Mock table data
        headers = ["Timestamp", "Metric 1", "Metric 2", "Status", "Actions"]
        rows = []

        for i in range(10):
            timestamp = (datetime.now() - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
            metric1 = f"{random.randint(50, 150)}"
            metric2 = f"{random.uniform(0.5, 2.0):.2f}"
            status = random.choice(["Active", "Inactive", "Warning", "Error"])
            actions = "View | Edit | Delete"
            rows.append([timestamp, metric1, metric2, status, actions])

        return {
            "headers": headers,
            "rows": rows
        }
    except Exception as e:
        logger.error(f"Error getting table data for {module_id}: {e}")
        return {"headers": [], "rows": []}


@api_v1.get("/modules/{module_id}/info")
async def get_module_detailed_info(module_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed module information."""
    try:
        base_info = await get_module_info(module_id)
        return {
            **base_info,
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "data_points": random.randint(1000, 10000),
            "description": base_info.get("description", "No description available")
        }
    except Exception as e:
        logger.error(f"Error getting module info for {module_id}: {e}")
        return {}


@api_v1.get("/modules/{module_id}/features")
async def get_module_features(module_id: str, current_user: User = Depends(get_current_user)):
    """Get module features."""
    try:
        # Mock features based on module type
        if "energy" in module_id:
            features = [
                {"name": "Real-time Monitoring", "description": "Continuous energy consumption tracking", "icon": "fas fa-eye"},
                {"name": "Predictive Analytics", "description": "AI-powered consumption forecasting", "icon": "fas fa-brain"},
                {"name": "Cost Optimization", "description": "Automatic cost reduction recommendations", "icon": "fas fa-euro-sign"},
                {"name": "Alert System", "description": "Smart notifications for anomalies", "icon": "fas fa-bell"}
            ]
        elif "ai" in module_id or "ml" in module_id:
            features = [
                {"name": "Model Training", "description": "Automated ML model training", "icon": "fas fa-graduation-cap"},
                {"name": "Performance Monitoring", "description": "Real-time model performance tracking", "icon": "fas fa-chart-line"},
                {"name": "Auto-tuning", "description": "Automatic hyperparameter optimization", "icon": "fas fa-sliders-h"},
                {"name": "Explainability", "description": "Model decision explanations", "icon": "fas fa-search"}
            ]
        else:
            features = [
                {"name": "Data Processing", "description": "High-performance data processing", "icon": "fas fa-database"},
                {"name": "Real-time Updates", "description": "Live data streaming", "icon": "fas fa-sync"},
                {"name": "API Integration", "description": "RESTful API endpoints", "icon": "fas fa-plug"},
                {"name": "Reporting", "description": "Automated report generation", "icon": "fas fa-file-alt"}
            ]

        return features
    except Exception as e:
        logger.error(f"Error getting features for {module_id}: {e}")
        return []


@api_v1.post("/modules/{module_id}/settings")
async def update_module_settings(module_id: str, settings: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update module settings."""
    try:
        # In a real implementation, this would save to database
        logger.info(f"Settings updated for module {module_id} by user {current_user.username}")
        return {"status": "settings_updated", "module_id": module_id}
    except Exception as e:
        logger.error(f"Error updating settings for {module_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")


@api_v1.get("/modules/{module_id}/logs")
async def get_module_logs(module_id: str, current_user: User = Depends(get_current_user)):
    """Get module logs."""
    try:
        # Mock logs
        logs = []
        for i in range(20):
            timestamp = (datetime.now() - timedelta(minutes=i*5)).isoformat()
            level = random.choice(["INFO", "WARNING", "ERROR"])
            message = f"Module {module_id} operation completed successfully"
            logs.append(f"[{timestamp}] {level}: {message}")

        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error getting logs for {module_id}: {e}")
        return {"logs": []}


# ============================================================================
# AR/VR ENDPOINTS
# ============================================================================

if ARVR_AVAILABLE:
    # Initialize AR/VR services
    # ar_guide = ARVRMaintenanceGuide()
    # vr_simulator = VRTrainingSimulator()
    # mr_dashboard = MixedRealityDashboard()
    pass

    # AR Maintenance Guide Endpoints
    @ar_router.post("/maintenance/session/start")
    async def start_ar_maintenance_session(
        procedure_id: str,
        technician_id: str,
        equipment_id: str,
        current_user: User = Depends(get_current_user),
    ):
        """Start AR maintenance session."""
        try:
            session = ar_guide.start_maintenance_session(
                procedure_id, technician_id, equipment_id
            )
            return {"status": "success", "session": session}
        except Exception as e:
            logger.error(f"AR session start failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session start failed: {str(e)}"
            )

    @ar_router.get("/maintenance/session/{session_id}/step")
    async def get_ar_maintenance_step(
        session_id: str, current_user: User = Depends(get_current_user)
    ):
        """Get current AR maintenance step."""
        try:
            step = ar_guide.get_current_step_guidance()
            return {"status": "success", "step": step}
        except Exception as e:
            logger.error(f"AR step retrieval failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Step retrieval failed: {str(e)}"
            )

    @ar_router.post("/maintenance/session/{session_id}/advance")
    async def advance_ar_maintenance_step(
        session_id: str,
        checkpoint_data: Optional[Dict[str, Any]] = None,
        current_user: User = Depends(get_current_user),
    ):
        """Advance to next AR maintenance step."""
        try:
            next_step = ar_guide.advance_step(checkpoint_data)
            return {"status": "success", "next_step": next_step}
        except Exception as e:
            logger.error(f"AR step advance failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Step advance failed: {str(e)}"
            )

    @ar_router.post("/maintenance/session/{session_id}/complete")
    async def complete_ar_maintenance_session(
        session_id: str, current_user: User = Depends(get_current_user)
    ):
        """Complete AR maintenance session."""
        try:
            completion = ar_guide.complete_session()
            return {"status": "success", "completion": completion}
        except Exception as e:
            logger.error(f"AR session completion failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session completion failed: {str(e)}"
            )

    @ar_router.get("/maintenance/procedures")
    async def get_ar_maintenance_procedures(
        equipment_type: Optional[str] = None,
        current_user: User = Depends(get_current_user),
    ):
        """Get available AR maintenance procedures."""
        try:
            procedures = ar_guide.get_available_procedures(equipment_type)
            return {"status": "success", "procedures": procedures}
        except Exception as e:
            logger.error(f"AR procedures retrieval failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Procedures retrieval failed: {str(e)}"
            )

    # VR Training Simulator Endpoints
    @vr_router.post("/training/session/start")
    async def start_vr_training_session(
        trainee_id: str,
        scenario_id: str,
        current_user: User = Depends(get_current_user),
    ):
        """Start VR training session."""
        try:
            session = vr_simulator.start_training_session(trainee_id, scenario_id)
            return {"status": "success", "session": session}
        except Exception as e:
            logger.error(f"VR session start failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session start failed: {str(e)}"
            )

    @vr_router.get("/training/session/{session_id}/state")
    async def get_vr_training_state(
        session_id: str, current_user: User = Depends(get_current_user)
    ):
        """Get VR training session state."""
        try:
            state = vr_simulator.get_session_state(session_id)
            return {"status": "success", "state": state}
        except Exception as e:
            logger.error(f"VR state retrieval failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"State retrieval failed: {str(e)}"
            )

    @vr_router.post("/training/session/{session_id}/submit")
    async def submit_vr_task_result(
        session_id: str,
        task_id: str,
        result_data: Dict[str, Any],
        current_user: User = Depends(get_current_user),
    ):
        """Submit VR task result."""
        try:
            evaluation = vr_simulator.submit_task_result(
                session_id, task_id, result_data
            )
            return {"status": "success", "evaluation": evaluation}
        except Exception as e:
            logger.error(f"VR task submission failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Task submission failed: {str(e)}"
            )

    @vr_router.post("/training/session/{session_id}/complete")
    async def complete_vr_training_session(
        session_id: str, current_user: User = Depends(get_current_user)
    ):
        """Complete VR training session."""
        try:
            completion = vr_simulator.complete_session(session_id)
            return {"status": "success", "completion": completion}
        except Exception as e:
            logger.error(f"VR session completion failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session completion failed: {str(e)}"
            )

    @vr_router.get("/training/scenarios")
    async def get_vr_training_scenarios(
        trainee_level: Optional[str] = None,
        current_user: User = Depends(get_current_user),
    ):
        """Get available VR training scenarios."""
        try:
            scenarios = vr_simulator.get_available_scenarios(trainee_level)
            return {"status": "success", "scenarios": scenarios}
        except Exception as e:
            logger.error(f"VR scenarios retrieval failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Scenarios retrieval failed: {str(e)}"
            )

    @vr_router.get("/training/progress/{trainee_id}")
    async def get_vr_trainee_progress(
        trainee_id: str, current_user: User = Depends(get_current_user)
    ):
        """Get VR training progress for trainee."""
        try:
            progress = vr_simulator.get_trainee_progress(trainee_id)
            return {"status": "success", "progress": progress}
        except Exception as e:
            logger.error(f"VR progress retrieval failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Progress retrieval failed: {str(e)}"
            )

    # Mixed Reality Dashboard Endpoints
    @mr_router.post("/dashboard/session/start")
    async def start_mr_dashboard_session(
        dashboard_id: str,
        user_id: str,
        workspace_context: Dict[str, Any],
        current_user: User = Depends(get_current_user),
    ):
        """Start MR dashboard session."""
        try:
            session = mr_dashboard.start_dashboard_session(
                dashboard_id, user_id, workspace_context
            )
            return {"status": "success", "session": session}
        except Exception as e:
            logger.error(f"MR session start failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session start failed: {str(e)}"
            )

    @mr_router.get("/dashboard/session/{session_id}/data/{widget_id}")
    async def get_mr_widget_data(
        session_id: str, widget_id: str, current_user: User = Depends(get_current_user)
    ):
        """Get MR widget data."""
        try:
            data = mr_dashboard.update_widget_data(session_id, widget_id)
            return {"status": "success", "data": data}
        except Exception as e:
            logger.error(f"MR widget data retrieval failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Widget data retrieval failed: {str(e)}"
            )

    @mr_router.post("/dashboard/session/{session_id}/interact")
    async def handle_mr_interaction(
        session_id: str,
        interaction_data: Dict[str, Any],
        current_user: User = Depends(get_current_user),
    ):
        """Handle MR dashboard interaction."""
        try:
            response = mr_dashboard.handle_user_interaction(
                session_id, interaction_data
            )
            return {"status": "success", "response": response}
        except Exception as e:
            logger.error(f"MR interaction handling failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Interaction handling failed: {str(e)}"
            )

    @mr_router.post("/dashboard/session/{session_id}/end")
    async def end_mr_dashboard_session(
        session_id: str, current_user: User = Depends(get_current_user)
    ):
        """End MR dashboard session."""
        try:
            summary = mr_dashboard.end_session(session_id)
            return {"status": "success", "summary": summary}
        except Exception as e:
            logger.error(f"MR session end failed: {e}")
            raise HTTPException(status_code=500, detail=f"Session end failed: {str(e)}")

    @mr_router.get("/dashboard/available")
    async def get_available_mr_dashboards(
        user_id: str, current_user: User = Depends(get_current_user)
    ):
        """Get available MR dashboards for user."""
        try:
            dashboards = mr_dashboard.get_available_dashboards(user_id)
            return {"status": "success", "dashboards": dashboards}
        except Exception as e:
            logger.error(f"MR dashboards retrieval failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Dashboards retrieval failed: {str(e)}"
            )


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        workers=settings.workers,
    )
