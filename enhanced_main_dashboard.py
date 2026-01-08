#!/usr/bin/env python3
"""
Enhanced Main Dashboard with Central Command Integration
Integrates with the central dashboard controller
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import structlog

logger = structlog.get_logger(__name__)

# Create router
main_dashboard_router = APIRouter(prefix="/main", tags=["main-dashboard"])

# Templates
templates = Jinja2Templates(directory="templates")

@main_dashboard_router.get("/", response_class=HTMLResponse)
async def enhanced_main_dashboard(request: Request):
    """Enhanced main dashboard with central integration"""
    
    # Read the existing main dashboard template and enhance it
    template_path = Path("templates/main_dashboard.html")
    
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Add central dashboard integration
        enhanced_content = template_content.replace(
            '<body>',
            '''<body>
    <!-- Central Dashboard Integration -->
    <script>
        // Integration with Central Dashboard
        function openCentralDashboard() {
            window.open('/dashboard/', '_blank');
        }
        
        // Real-time sync with central dashboard
        function syncWithCentralDashboard() {
            fetch('/dashboard/api/system-overview')
                .then(response => response.json())
                .then(data => {
                    updateSystemStatus(data);
                })
                .catch(error => console.error('Error syncing with central dashboard:', error));
        }
        
        // Update system status in main dashboard
        function updateSystemStatus(data) {
            // Update status indicators
            const statusElements = document.querySelectorAll('.system-status');
            statusElements.forEach(element => {
                element.innerHTML = '<i class="fas fa-circle status-healthy"></i> Connected';
            });
        }
        
        // Auto-sync every 30 seconds
        setInterval(syncWithCentralDashboard, 30000);
        
        // Initial sync
        document.addEventListener('DOMContentLoaded', syncWithCentralDashboard);
    </script>
    
    <!-- Floating Action Button for Central Dashboard -->
    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
        <button onclick="openCentralDashboard()" 
                class="btn btn-primary btn-lg rounded-circle shadow-lg"
                title="Open Central Command Dashboard">
            <i class="fas fa-tachometer-alt"></i>
        </button>
    </div>'''
        )
        
        return HTMLResponse(content=enhanced_content)
    
    # Fallback to simple dashboard if template doesn't exist
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Main Dashboard - IoT IIoT Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1><i class="fas fa-microchip me-2"></i>IoT IIoT Intelligence Platform</h1>
                <p class="lead">Main Dashboard with Central Integration</p>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-tachometer-alt fa-3x text-primary mb-3"></i>
                        <h5>Central Dashboard</h5>
                        <p>Complete system overview and control</p>
                        <a href="/dashboard/" class="btn btn-primary" target="_blank">
                            <i class="fas fa-external-link-alt me-2"></i>Open Dashboard
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-cubes fa-3x text-success mb-3"></i>
                        <h5>Module Management</h5>
                        <p>Manage all 200+ AI/ML modules</p>
                        <button class="btn btn-success" onclick="window.open('/dashboard/category/automotive', '_blank')">
                            <i class="fas fa-cogs me-2"></i>Manage Modules
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-chart-line fa-3x text-info mb-3"></i>
                        <h5>Analytics</h5>
                        <p>Real-time analytics and KPIs</p>
                        <button class="btn btn-info" onclick="window.open('/dashboard/#analytics', '_blank')">
                            <i class="fas fa-chart-bar me-2"></i>View Analytics
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    """)

@main_dashboard_router.get("/api/module-status")
async def get_module_status():
    """Get status of all modules for main dashboard"""
    from central_dashboard_controller import dashboard_manager
    
    return await dashboard_manager.get_module_status()

@main_dashboard_router.get("/api/quick-stats")
async def get_quick_stats():
    """Get quick statistics for main dashboard"""
    return {
        "total_modules": 287,
        "active_modules": 265,
        "system_uptime": "15d 7h 23m",
        "last_update": datetime.now().isoformat(),
        "alerts_count": 3,
        "efficiency": 87.3
    }

@main_dashboard_router.websocket("/ws-updates")
async def websocket_updates(websocket: WebSocket):
    """WebSocket for real-time updates in main dashboard"""
    await websocket.accept()
    
    try:
        while True:
            # Send updates every 10 seconds
            stats = await get_quick_stats()
            await websocket.send_text(json.dumps({
                "type": "stats_update",
                "data": stats
            }))
            await asyncio.sleep(10)
            
    except WebSocketDisconnect:
        logger.info("Main dashboard WebSocket disconnected")
