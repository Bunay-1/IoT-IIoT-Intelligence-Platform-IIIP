#!/usr/bin/env python3
"""
Enhanced Module Integration Service for Central Dashboard
Extends existing module integration with dashboard-specific features
"""

import asyncio
import importlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)

class DashboardModuleIntegration:
    """Enhanced module integration for central dashboard"""
    
    def __init__(self):
        self.loaded_modules = {}
        self.module_metadata = {}
        self.dashboard_modules = {}
        
    async def discover_all_modules(self) -> Dict[str, Any]:
        """Discover all available modules for dashboard"""
        src_path = Path("src")
        modules = {}
        
        for file_path in src_path.glob("*.py"):
            if file_path.name.startswith("__") or file_path.name in [
                "central_dashboard_controller.py", 
                "enhanced_main_dashboard.py",
                "module_integration_service.py"
            ]:
                continue
                
            module_name = file_path.stem
            module_info = {
                "name": module_name,
                "file_path": str(file_path),
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "has_template": f"{module_name}.html" in [f.name for f in Path("templates").iterdir()],
                "category": self._categorize_module(module_name),
                "status": "discovered"
            }
            
            modules[module_name] = module_info
            
        logger.info(f"Discovered {len(modules)} modules for dashboard")
        return modules
    
    def _categorize_module(self, module_name: str) -> str:
        """Categorize module based on name patterns"""
        categories = {
            "automotive": ["automotive", "apqp", "ppap", "spc", "quality"],
            "chemical": ["chemical", "safety", "hazop", "sil"],
            "energy": ["energy", "trading", "marketplace", "optimization"],
            "pharma": ["pharma", "compliance", "gmp", "fda"],
            "sales": ["sales", "crm", "channel", "customer"],
            "ai_ml": ["ai", "ml", "automl", "reinforcement", "neural", "model"],
            "industrial": ["industrial", "cnc", "digital_twin", "iot", "edge"],
            "security": ["security", "audit", "auth", "zero_trust"],
            "analytics": ["analytics", "dashboard", "metrics", "kpi"],
            "monitoring": ["monitor", "alert", "health", "performance"]
        }
        
        module_lower = module_name.lower()
        
        for category, keywords in categories.items():
            if any(keyword in module_lower for keyword in keywords):
                return category
                
        return "other"
    
    async def get_dashboard_modules(self) -> Dict[str, Any]:
        """Get modules organized for dashboard display"""
        all_modules = await self.discover_all_modules()
        
        # Organize by category
        categorized = {}
        for module_name, module_info in all_modules.items():
            category = module_info["category"]
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(module_info)
        
        # Add category metadata
        category_info = {
            "automotive": {
                "name": "🚗 Automotive Quality",
                "icon": "fa-car",
                "color": "#007bff",
                "description": "Automotive quality control and compliance"
            },
            "chemical": {
                "name": "⚗️ Chemical Process",
                "icon": "fa-flask", 
                "color": "#28a745",
                "description": "Chemical process safety and management"
            },
            "energy": {
                "name": "⚡ Energy Trading",
                "icon": "fa-bolt",
                "color": "#ffc107", 
                "description": "Energy trading and optimization"
            },
            "pharma": {
                "name": "💊 Pharma Compliance",
                "icon": "fa-pills",
                "color": "#17a2b8",
                "description": "Pharmaceutical compliance and quality"
            },
            "sales": {
                "name": "💰 Sales & CRM",
                "icon": "fa-chart-line",
                "color": "#6f42c1",
                "description": "Sales channel management and analytics"
            },
            "ai_ml": {
                "name": "🤖 AI/ML Core",
                "icon": "fa-brain",
                "color": "#e83e8c",
                "description": "Core AI and machine learning modules"
            },
            "industrial": {
                "name": "🏭 Industrial IoT",
                "icon": "fa-industry",
                "color": "#fd7e14",
                "description": "Industrial IoT and manufacturing"
            },
            "security": {
                "name": "🔒 Security & Compliance",
                "icon": "fa-shield-alt",
                "color": "#dc3545",
                "description": "Security, audit and compliance modules"
            },
            "analytics": {
                "name": "📊 Analytics",
                "icon": "fa-chart-bar",
                "color": "#20c997",
                "description": "Analytics and reporting modules"
            },
            "monitoring": {
                "name": "📡 Monitoring",
                "icon": "fa-satellite-dish",
                "color": "#6f42c1",
                "description": "System monitoring and alerting"
            },
            "other": {
                "name": "🔧 Other",
                "icon": "fa-cogs",
                "color": "#6c757d",
                "description": "Other specialized modules"
            }
        }
        
        # Combine categories with info
        dashboard_data = {}
        for category, modules in categorized.items():
            dashboard_data[category] = {
                **category_info.get(category, category_info["other"]),
                "modules": modules,
                "count": len(modules),
                "active_count": len([m for m in modules if m["has_template"]])
            }
        
        return dashboard_data
    
    async def launch_module_from_dashboard(self, module_name: str) -> Dict[str, Any]:
        """Launch module from dashboard interface"""
        try:
            # Check if module exists
            module_path = Path(f"src/{module_name}.py")
            template_path = Path(f"templates/{module_name}.html")
            
            if not module_path.exists():
                return {
                    "success": False,
                    "error": f"Module {module_name} not found"
                }
            
            # Try to load module
            try:
                module = importlib.import_module(f"src.{module_name}")
                
                # Extract basic info
                info = {
                    "name": module_name,
                    "description": getattr(module, "__doc__", "No description available"),
                    "has_router": hasattr(module, 'router'),
                    "has_app": hasattr(module, 'app'),
                    "has_main": hasattr(module, 'main')
                }
                
            except Exception as e:
                info = {
                    "name": module_name,
                    "load_error": str(e),
                    "status": "load_failed"
                }
            
            return {
                "success": True,
                "module": module_name,
                "info": info,
                "has_gui": template_path.exists(),
                "gui_url": f"/{module_name.replace('_', '-')}" if template_path.exists() else None,
                "category": self._categorize_module(module_name)
            }
            
        except Exception as e:
            logger.error(f"Failed to launch module {module_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_module_quick_actions(self, module_name: str) -> List[Dict[str, Any]]:
        """Get quick actions for a module"""
        actions = []
        
        # Common actions
        actions.extend([
            {
                "name": "View Documentation",
                "icon": "fa-book",
                "action": f"open_docs('{module_name}')",
                "type": "info"
            },
            {
                "name": "View Source Code",
                "icon": "fa-code",
                "action": f"view_source('{module_name}')",
                "type": "info"
            },
            {
                "name": "Test Module",
                "icon": "fa-vial",
                "action": f"test_module('{module_name}')",
                "type": "action"
            }
        ])
        
        # Check for GUI
        if Path(f"templates/{module_name}.html").exists():
            actions.append({
                "name": "Open GUI",
                "icon": "fa-desktop",
                "action": f"open_gui('{module_name}')",
                "type": "primary"
            })
        
        # Check for API endpoints
        try:
            module = importlib.import_module(f"src.{module_name}")
            if hasattr(module, 'router'):
                actions.append({
                    "name": "View API Endpoints",
                    "icon": "fa-plug",
                    "action": f"view_endpoints('{module_name}')",
                    "type": "info"
                })
        except:
            pass
        
        return actions

# Global instance
dashboard_module_integration = DashboardModuleIntegration()
