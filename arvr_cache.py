"""
AR/VR Cache Module

This module implements caching system for AR/VR content including:
- 3D model caching
- Texture and material caching
- Scene data caching
- Performance optimization
- Memory management
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.logging_config import get_logger

logger = get_logger(__name__)


class ARVRCache:
    """AR/VR content caching system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.model_cache = {}
        self.texture_cache = {}
        self.scene_cache = {}
        self.material_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_usage": 0
        }
        
    def _default_config(self) -> Dict[str, Any]:
        """Default cache configuration."""
        return {
            "max_memory_mb": 2048,  # 2GB
            "max_items": 1000,
            "ttl_seconds": 3600,  # 1 hour
            "compression_enabled": True,
            "preload_common": True,
            "cleanup_interval": 300  # 5 minutes
        }
    
    def cache_model(
        self,
        model_id: str,
        model_data: Dict[str, Any],
        priority: str = "normal"
    ) -> bool:
        """Cache 3D model data."""
        # Check memory constraints
        model_size = len(json.dumps(model_data).encode())
        if not self._check_memory_available(model_size):
            self._evict_old_items()
        
        cache_entry = {
            "model_id": model_id,
            "data": model_data,
            "size": model_size,
            "priority": priority,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 0
        }
        
        self.model_cache[model_id] = cache_entry
        self.cache_stats["memory_usage"] += model_size
        
        logger.debug(f"Model cached: {model_id} ({model_size} bytes)")
        return True
    
    def get_cached_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get cached 3D model."""
        if model_id in self.model_cache:
            cache_entry = self.model_cache[model_id]
            
            # Check TTL
            if self._is_expired(cache_entry):
                del self.model_cache[model_id]
                self.cache_stats["misses"] += 1
                return None
            
            # Update access stats
            cache_entry["last_accessed"] = datetime.now()
            cache_entry["access_count"] += 1
            self.cache_stats["hits"] += 1
            
            logger.debug(f"Model cache hit: {model_id}")
            return cache_entry["data"]
        
        self.cache_stats["misses"] += 1
        return None
    
    def cache_texture(
        self,
        texture_id: str,
        texture_data: Dict[str, Any],
        resolution: str = "high"
    ) -> bool:
        """Cache texture data."""
        texture_size = len(json.dumps(texture_data).encode())
        if not self._check_memory_available(texture_size):
            self._evict_old_items()
        
        cache_entry = {
            "texture_id": texture_id,
            "data": texture_data,
            "size": texture_size,
            "resolution": resolution,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 0
        }
        
        self.texture_cache[texture_id] = cache_entry
        self.cache_stats["memory_usage"] += texture_size
        
        logger.debug(f"Texture cached: {texture_id} ({texture_size} bytes)")
        return True
    
    def get_cached_texture(self, texture_id: str) -> Optional[Dict[str, Any]]:
        """Get cached texture."""
        if texture_id in self.texture_cache:
            cache_entry = self.texture_cache[texture_id]
            
            if self._is_expired(cache_entry):
                del self.texture_cache[texture_id]
                self.cache_stats["misses"] += 1
                return None
            
            cache_entry["last_accessed"] = datetime.now()
            cache_entry["access_count"] += 1
            self.cache_stats["hits"] += 1
            
            logger.debug(f"Texture cache hit: {texture_id}")
            return cache_entry["data"]
        
        self.cache_stats["misses"] += 1
        return None
    
    def cache_scene(
        self,
        scene_id: str,
        scene_data: Dict[str, Any],
        scene_type: str = "static"
    ) -> bool:
        """Cache scene data."""
        scene_size = len(json.dumps(scene_data).encode())
        if not self._check_memory_available(scene_size):
            self._evict_old_items()
        
        cache_entry = {
            "scene_id": scene_id,
            "data": scene_data,
            "size": scene_size,
            "scene_type": scene_type,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 0
        }
        
        self.scene_cache[scene_id] = cache_entry
        self.cache_stats["memory_usage"] += scene_size
        
        logger.debug(f"Scene cached: {scene_id} ({scene_size} bytes)")
        return True
    
    def get_cached_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """Get cached scene."""
        if scene_id in self.scene_cache:
            cache_entry = self.scene_cache[scene_id]
            
            if self._is_expired(cache_entry):
                del self.scene_cache[scene_id]
                self.cache_stats["misses"] += 1
                return None
            
            cache_entry["last_accessed"] = datetime.now()
            cache_entry["access_count"] += 1
            self.cache_stats["hits"] += 1
            
            logger.debug(f"Scene cache hit: {scene_id}")
            return cache_entry["data"]
        
        self.cache_stats["misses"] += 1
        return None
    
    def cache_material(
        self,
        material_id: str,
        material_data: Dict[str, Any],
        material_type: str = "pbr"
    ) -> bool:
        """Cache material data."""
        material_size = len(json.dumps(material_data).encode())
        if not self._check_memory_available(material_size):
            self._evict_old_items()
        
        cache_entry = {
            "material_id": material_id,
            "data": material_data,
            "size": material_size,
            "material_type": material_type,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 0
        }
        
        self.material_cache[material_id] = cache_entry
        self.cache_stats["memory_usage"] += material_size
        
        logger.debug(f"Material cached: {material_id} ({material_size} bytes)")
        return True
    
    def get_cached_material(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Get cached material."""
        if material_id in self.material_cache:
            cache_entry = self.material_cache[material_id]
            
            if self._is_expired(cache_entry):
                del self.material_cache[material_id]
                self.cache_stats["misses"] += 1
                return None
            
            cache_entry["last_accessed"] = datetime.now()
            cache_entry["access_count"] += 1
            self.cache_stats["hits"] += 1
            
            logger.debug(f"Material cache hit: {material_id}")
            return cache_entry["data"]
        
        self.cache_stats["misses"] += 1
        return None
    
    def _check_memory_available(self, required_size: int) -> bool:
        """Check if memory is available for caching."""
        max_memory_bytes = self.config["max_memory_mb"] * 1024 * 1024
        return (self.cache_stats["memory_usage"] + required_size) <= max_memory_bytes
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        age = datetime.now() - cache_entry["created_at"]
        return age.total_seconds() > self.config["ttl_seconds"]
    
    def _evict_old_items(self):
        """Evict old items from cache based on LRU and priority."""
        all_items = []
        
        # Collect all cache items
        for cache_dict in [self.model_cache, self.texture_cache, self.scene_cache, self.material_cache]:
            for item_id, cache_entry in cache_dict.items():
                all_items.append((item_id, cache_entry, cache_dict))
        
        # Sort by priority and last accessed time
        priority_order = {"low": 0, "normal": 1, "high": 2, "critical": 3}
        
        all_items.sort(key=lambda x: (
            priority_order.get(x[1].get("priority", "normal"), 1),
            x[1]["last_accessed"]
        ))
        
        # Evict items until memory is available
        evicted_count = 0
        for item_id, cache_entry, cache_dict in all_items:
            if self.cache_stats["memory_usage"] <= self.config["max_memory_mb"] * 1024 * 1024 * 0.8:
                break
            
            del cache_dict[item_id]
            self.cache_stats["memory_usage"] -= cache_entry["size"]
            self.cache_stats["evictions"] += 1
            evicted_count += 1
        
        if evicted_count > 0:
            logger.info(f"Cache eviction: removed {evicted_count} items")
    
    def preload_common_assets(self, asset_list: List[Dict[str, Any]]):
        """Preload commonly used assets."""
        if not self.config["preload_common"]:
            return
        
        for asset in asset_list:
            asset_type = asset.get("type")
            asset_id = asset.get("id")
            asset_data = asset.get("data")
            
            if asset_type == "model" and asset_id and asset_data:
                self.cache_model(asset_id, asset_data, "high")
            elif asset_type == "texture" and asset_id and asset_data:
                self.cache_texture(asset_id, asset_data, asset.get("resolution", "high"))
            elif asset_type == "scene" and asset_id and asset_data:
                self.cache_scene(asset_id, asset_data, asset.get("scene_type", "static"))
            elif asset_type == "material" and asset_id and asset_data:
                self.cache_material(asset_id, asset_data, asset.get("material_type", "pbr"))
        
        logger.info(f"Preloaded {len(asset_list)} common assets")
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """Clear cache entries."""
        if cache_type == "model" or cache_type is None:
            cleared_models = len(self.model_cache)
            self.model_cache.clear()
            logger.info(f"Cleared {cleared_models} models from cache")
        
        if cache_type == "texture" or cache_type is None:
            cleared_textures = len(self.texture_cache)
            self.texture_cache.clear()
            logger.info(f"Cleared {cleared_textures} textures from cache")
        
        if cache_type == "scene" or cache_type is None:
            cleared_scenes = len(self.scene_cache)
            self.scene_cache.clear()
            logger.info(f"Cleared {cleared_scenes} scenes from cache")
        
        if cache_type == "material" or cache_type is None:
            cleared_materials = len(self.material_cache)
            self.material_cache.clear()
            logger.info(f"Cleared {cleared_materials} materials from cache")
        
        # Reset memory usage
        self.cache_stats["memory_usage"] = 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_stats["hits"],
            "cache_misses": self.cache_stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.cache_stats["evictions"],
            "memory_usage_mb": self.cache_stats["memory_usage"] / (1024 * 1024),
            "memory_usage_percent": (self.cache_stats["memory_usage"] / (self.config["max_memory_mb"] * 1024 * 1024)) * 100,
            "cached_models": len(self.model_cache),
            "cached_textures": len(self.texture_cache),
            "cached_scenes": len(self.scene_cache),
            "cached_materials": len(self.material_cache),
            "total_cached_items": len(self.model_cache) + len(self.texture_cache) + len(self.scene_cache) + len(self.material_cache)
        }
    
    def optimize_cache(self):
        """Optimize cache performance."""
        # Remove expired items
        expired_count = 0
        
        for cache_dict in [self.model_cache, self.texture_cache, self.scene_cache, self.material_cache]:
            expired_items = [
                item_id for item_id, cache_entry in cache_dict.items()
                if self._is_expired(cache_entry)
            ]
            
            for item_id in expired_items:
                self.cache_stats["memory_usage"] -= cache_dict[item_id]["size"]
                del cache_dict[item_id]
                expired_count += 1
        
        # Evict items if over memory limit
        if self.cache_stats["memory_usage"] > self.config["max_memory_mb"] * 1024 * 1024 * 0.9:
            self._evict_old_items()
        
        logger.info(f"Cache optimization: removed {expired_count} expired items")


# Global AR/VR cache instance
arvr_cache = ARVRCache()


def cache_arvr_model(
    model_id: str,
    model_data: Dict[str, Any],
    priority: str = "normal"
) -> bool:
    """Cache 3D model data."""
    return arvr_cache.cache_model(model_id, model_data, priority)


def get_cached_arvr_model(model_id: str) -> Optional[Dict[str, Any]]:
    """Get cached 3D model."""
    return arvr_cache.get_cached_model(model_id)


def cache_arvr_texture(
    texture_id: str,
    texture_data: Dict[str, Any],
    resolution: str = "high"
) -> bool:
    """Cache texture data."""
    return arvr_cache.cache_texture(texture_id, texture_data, resolution)


def get_cached_arvr_texture(texture_id: str) -> Optional[Dict[str, Any]]:
    """Get cached texture."""
    return arvr_cache.get_cached_texture(texture_id)


def cache_arvr_scene(
    scene_id: str,
    scene_data: Dict[str, Any],
    scene_type: str = "static"
) -> bool:
    """Cache scene data."""
    return arvr_cache.cache_scene(scene_id, scene_data, scene_type)


def get_cached_arvr_scene(scene_id: str) -> Optional[Dict[str, Any]]:
    """Get cached scene."""
    return arvr_cache.get_cached_scene(scene_id)


def cache_arvr_material(
    material_id: str,
    material_data: Dict[str, Any],
    material_type: str = "pbr"
) -> bool:
    """Cache material data."""
    return arvr_cache.cache_material(material_id, material_data, material_type)


def get_cached_arvr_material(material_id: str) -> Optional[Dict[str, Any]]:
    """Get cached material."""
    return arvr_cache.get_cached_material(material_id)


def get_arvr_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics."""
    return arvr_cache.get_cache_stats()


def optimize_arvr_cache():
    """Optimize cache performance."""
    arvr_cache.optimize_cache()
