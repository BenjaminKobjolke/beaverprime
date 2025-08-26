"""
Performance configuration for BeaverHabits application.

This module provides configuration settings and utilities for managing
performance optimization features like caching, monitoring, and bulk operations.
"""

import os
from typing import Dict, Any


class PerformanceConfig:
    """Configuration settings for performance optimizations."""
    
    # Cache settings
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    CACHE_DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL", "300"))  # 5 minutes
    CALCULATION_CACHE_TTL: int = int(os.getenv("CALCULATION_CACHE_TTL", "600"))  # 10 minutes
    MAX_CACHE_ENTRIES: int = int(os.getenv("MAX_CACHE_ENTRIES", "1000"))
    
    # Monitoring settings
    ENABLE_PERFORMANCE_MONITORING: bool = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
    SLOW_QUERY_THRESHOLD_MS: int = int(os.getenv("SLOW_QUERY_THRESHOLD_MS", "100"))
    SLOW_ENDPOINT_THRESHOLD_MS: int = int(os.getenv("SLOW_ENDPOINT_THRESHOLD_MS", "1000"))
    MAX_METRICS_RETENTION: int = int(os.getenv("MAX_METRICS_RETENTION", "1000"))
    
    # Bulk operation settings
    ENABLE_BULK_OPERATIONS: bool = os.getenv("ENABLE_BULK_OPERATIONS", "true").lower() == "true"
    BULK_QUERY_BATCH_SIZE: int = int(os.getenv("BULK_QUERY_BATCH_SIZE", "100"))
    PRELOAD_RECENT_CHECKS_DAYS: int = int(os.getenv("PRELOAD_RECENT_CHECKS_DAYS", "90"))
    
    # Database optimization settings
    USE_CACHED_UOW: bool = os.getenv("USE_CACHED_UOW", "true").lower() == "true"
    ENABLE_EAGER_LOADING: bool = os.getenv("ENABLE_EAGER_LOADING", "true").lower() == "true"
    CONNECTION_POOL_SIZE: int = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
    CONNECTION_POOL_OVERFLOW: int = int(os.getenv("CONNECTION_POOL_OVERFLOW", "10"))
    
    # Feature flags
    ENABLE_OPTIMIZED_ROUTES: bool = os.getenv("ENABLE_OPTIMIZED_ROUTES", "false").lower() == "true"
    ENABLE_PERFORMANCE_DASHBOARD: bool = os.getenv("ENABLE_PERFORMANCE_DASHBOARD", "false").lower() == "true"
    ENABLE_WEEK_PRELOADING: bool = os.getenv("ENABLE_WEEK_PRELOADING", "true").lower() == "true"
    
    @classmethod
    def get_cache_config(cls) -> Dict[str, Any]:
        """Get cache configuration settings."""
        return {
            'enabled': cls.ENABLE_CACHING,
            'default_ttl': cls.CACHE_DEFAULT_TTL,
            'calculation_ttl': cls.CALCULATION_CACHE_TTL,
            'max_entries': cls.MAX_CACHE_ENTRIES
        }
    
    @classmethod
    def get_monitoring_config(cls) -> Dict[str, Any]:
        """Get monitoring configuration settings."""
        return {
            'enabled': cls.ENABLE_PERFORMANCE_MONITORING,
            'slow_query_threshold_ms': cls.SLOW_QUERY_THRESHOLD_MS,
            'slow_endpoint_threshold_ms': cls.SLOW_ENDPOINT_THRESHOLD_MS,
            'max_metrics_retention': cls.MAX_METRICS_RETENTION
        }
    
    @classmethod
    def get_bulk_operation_config(cls) -> Dict[str, Any]:
        """Get bulk operation configuration settings."""
        return {
            'enabled': cls.ENABLE_BULK_OPERATIONS,
            'batch_size': cls.BULK_QUERY_BATCH_SIZE,
            'preload_days': cls.PRELOAD_RECENT_CHECKS_DAYS
        }
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database optimization configuration settings."""
        return {
            'use_cached_uow': cls.USE_CACHED_UOW,
            'enable_eager_loading': cls.ENABLE_EAGER_LOADING,
            'pool_size': cls.CONNECTION_POOL_SIZE,
            'pool_overflow': cls.CONNECTION_POOL_OVERFLOW
        }
    
    @classmethod
    def get_feature_flags(cls) -> Dict[str, bool]:
        """Get feature flag settings."""
        return {
            'optimized_routes': cls.ENABLE_OPTIMIZED_ROUTES,
            'performance_dashboard': cls.ENABLE_PERFORMANCE_DASHBOARD,
            'week_preloading': cls.ENABLE_WEEK_PRELOADING
        }
    
    @classmethod
    def should_use_optimization(cls, optimization_name: str) -> bool:
        """Check if a specific optimization should be used."""
        optimization_flags = {
            'caching': cls.ENABLE_CACHING,
            'monitoring': cls.ENABLE_PERFORMANCE_MONITORING,
            'bulk_operations': cls.ENABLE_BULK_OPERATIONS,
            'cached_uow': cls.USE_CACHED_UOW,
            'eager_loading': cls.ENABLE_EAGER_LOADING,
            'optimized_routes': cls.ENABLE_OPTIMIZED_ROUTES,
            'performance_dashboard': cls.ENABLE_PERFORMANCE_DASHBOARD,
            'week_preloading': cls.ENABLE_WEEK_PRELOADING
        }
        
        return optimization_flags.get(optimization_name, False)
    
    @classmethod
    def print_config_summary(cls) -> str:
        """Get a summary of current performance configuration."""
        summary = [
            "Performance Configuration Summary:",
            f"├─ Caching: {'✓' if cls.ENABLE_CACHING else '✗'} (TTL: {cls.CACHE_DEFAULT_TTL}s)",
            f"├─ Monitoring: {'✓' if cls.ENABLE_PERFORMANCE_MONITORING else '✗'} (Slow Query: {cls.SLOW_QUERY_THRESHOLD_MS}ms)",
            f"├─ Bulk Operations: {'✓' if cls.ENABLE_BULK_OPERATIONS else '✗'} (Batch: {cls.BULK_QUERY_BATCH_SIZE})",
            f"├─ Cached UoW: {'✓' if cls.USE_CACHED_UOW else '✗'}",
            f"├─ Eager Loading: {'✓' if cls.ENABLE_EAGER_LOADING else '✗'}",
            f"├─ Optimized Routes: {'✓' if cls.ENABLE_OPTIMIZED_ROUTES else '✗'}",
            f"├─ Performance Dashboard: {'✓' if cls.ENABLE_PERFORMANCE_DASHBOARD else '✗'}",
            f"└─ Week Preloading: {'✓' if cls.ENABLE_WEEK_PRELOADING else '✗'}"
        ]
        return '\n'.join(summary)


# Global performance configuration instance
performance_config = PerformanceConfig()


def initialize_performance_features():
    """
    Initialize performance features based on configuration.
    
    This function should be called during application startup to enable
    the configured performance optimizations.
    """
    from beaverhabits.logging import logger
    
    logger.info("Initializing performance features...")
    logger.info(f"\n{performance_config.print_config_summary()}")
    
    # Start background tasks if enabled
    if performance_config.ENABLE_CACHING:
        from beaverhabits.services import start_cache_cleanup
        start_cache_cleanup()
        logger.info("Started cache cleanup background task")
    
    if performance_config.ENABLE_PERFORMANCE_MONITORING:
        from beaverhabits.services.monitoring_service import start_performance_monitoring
        start_performance_monitoring()
        logger.info("Started performance monitoring background task")
    
    logger.info("Performance features initialization complete")


def cleanup_performance_features():
    """
    Cleanup performance features during application shutdown.
    
    This function should be called during application shutdown to properly
    cleanup background tasks and resources.
    """
    from beaverhabits.logging import logger
    
    logger.info("Cleaning up performance features...")
    
    if performance_config.ENABLE_CACHING:
        from beaverhabits.services import stop_cache_cleanup
        stop_cache_cleanup()
        logger.info("Stopped cache cleanup background task")
    
    if performance_config.ENABLE_PERFORMANCE_MONITORING:
        from beaverhabits.services.monitoring_service import stop_performance_monitoring
        stop_performance_monitoring()
        logger.info("Stopped performance monitoring background task")
    
    logger.info("Performance features cleanup complete")


# Environment variable documentation
ENVIRONMENT_VARIABLES_HELP = """
Performance Configuration Environment Variables:

Caching:
  ENABLE_CACHING=true|false           Enable/disable caching (default: true)
  CACHE_DEFAULT_TTL=300               Default cache TTL in seconds (default: 300)
  CALCULATION_CACHE_TTL=600           Calculation cache TTL in seconds (default: 600)
  MAX_CACHE_ENTRIES=1000              Maximum cache entries (default: 1000)

Monitoring:
  ENABLE_PERFORMANCE_MONITORING=true|false  Enable performance monitoring (default: true)
  SLOW_QUERY_THRESHOLD_MS=100               Slow query threshold in ms (default: 100)
  SLOW_ENDPOINT_THRESHOLD_MS=1000           Slow endpoint threshold in ms (default: 1000)
  MAX_METRICS_RETENTION=1000                Maximum metrics to retain (default: 1000)

Bulk Operations:
  ENABLE_BULK_OPERATIONS=true|false    Enable bulk operations (default: true)
  BULK_QUERY_BATCH_SIZE=100           Bulk query batch size (default: 100)
  PRELOAD_RECENT_CHECKS_DAYS=90       Days of recent checks to preload (default: 90)

Database:
  USE_CACHED_UOW=true|false           Use cached Unit of Work (default: true)
  ENABLE_EAGER_LOADING=true|false     Enable eager loading (default: true)
  CONNECTION_POOL_SIZE=20             Connection pool size (default: 20)
  CONNECTION_POOL_OVERFLOW=10         Connection pool overflow (default: 10)

Features:
  ENABLE_OPTIMIZED_ROUTES=true|false     Enable optimized routes (default: false)
  ENABLE_PERFORMANCE_DASHBOARD=true|false Enable performance dashboard (default: false)
  ENABLE_WEEK_PRELOADING=true|false      Enable week preloading (default: true)
"""