# Changelog

All notable changes to this project will be documented in this file.

## [0.1.9] - 2025-10-02

### Added

- **Docs & Badges**: Added Docker Hub badges and updated deployment guides with Docker Hub build instructions
- **Signal Test Resilience**: Hardened system tests for signal metrics in CI Docker runs

### Changed

- **Image Tags**: Updated documentation, manifests, and guides to default to `0.1.9`
- **Kind Smoke Tests**: Generalized local image rewrites in CI to accept any pinned tag

### Fixed

- **Kubernetes Apply Steps**: Cleaned broken glob instructions and Redis defaults in `k8s/README.md`

## [0.1.8] - 2025-10-01

### Added

- **Docker Sidecar Support**: Production-ready Docker images with multi-architecture support (AMD64, ARM64)
  - Pre-built images available on Docker Hub: `princekrroshan01/gunicorn-prometheus-exporter`
  - Sidecar pattern for Kubernetes deployments with security contexts
  - Complete Docker Compose stack with Prometheus and Grafana
- **Kubernetes Manifests**: Production-ready K8s deployments with Redis, Prometheus, and Grafana
- **GitHub Actions CI/CD**: Automated multi-arch Docker builds and testing
- **Comprehensive Documentation**: Docker Hub README, Kubernetes guides, and deployment examples

### Changed

- **Metrics Server Binding**: Updated to support configurable bind address for Docker compatibility

## [0.1.7] - 2025-09-30

### Added

- **YAML Configuration Support**: Complete YAML-based configuration system for structured, readable configuration management
  - **YamlConfigLoader**: New class for loading, validating, and converting YAML configuration files
  - **load_yaml_config()**: Public API function for easy YAML configuration loading in Gunicorn config files
  - **Environment Variable Override**: YAML configuration values can be overridden by environment variables
  - **Comprehensive Validation**: Clear error messages for missing or invalid YAML configuration
  - **Backward Compatibility**: Full compatibility with existing environment variable configuration
- **YAML Configuration Examples**: Complete set of example YAML configurations for different use cases
  - **Basic Configuration**: Simple setup for development and testing
  - **Redis Configuration**: Production setup with Redis storage backend
  - **SSL Configuration**: Secure setup with SSL/TLS encryption
  - **Production Configuration**: Comprehensive production-ready configuration
- **Enhanced Documentation**: Complete documentation suite for YAML configuration
  - **YAML Configuration Guide**: Comprehensive guide covering structure, examples, and best practices
  - **API Reference Updates**: Updated hooks and configuration API references with YAML support
  - **Setup Guide Updates**: Added YAML configuration as recommended option
  - **Migration Guide**: Step-by-step migration from environment variables to YAML
- **System Testing Enhancements**: Docker-based system tests for YAML configuration validation
  - **YAML System Tests**: Complete end-to-end testing of YAML configuration loading
  - **Docker Integration**: Docker-based testing for consistent environment validation
  - **CI/CD Integration**: GitHub Actions workflow for automated YAML configuration testing
  - **Comprehensive Validation**: Testing of all YAML configuration scenarios and error handling

### Changed

- **Configuration Architecture**: Enhanced ConfigManager to support YAML configuration loading with environment variable override
- **Documentation Structure**: Updated all documentation to prioritize YAML configuration while maintaining environment variable support
- **Setup Process**: YAML configuration now recommended as primary configuration method
- **API Surface**: Added new public API functions for YAML configuration loading

### Fixed

- **Docker System Tests**: Fixed Docker vs local configuration path consistency issues
- **Gunicorn Bind Address**: Fixed Gunicorn bind address for Docker compatibility (0.0.0.0 instead of 127.0.0.1)
- **Environment Variable Handling**: Fixed VENV_DIR printing when undefined in Docker mode
- **Configuration Validation**: Enhanced validation with clear error messages for YAML configuration

### Technical Details

- **YAML Structure**: Hierarchical configuration structure with exporter.prometheus, exporter.gunicorn, exporter.redis, exporter.ssl, and exporter.cleanup sections
- **Configuration Loading**: YAML configuration is loaded first, then environment variables can override specific values
- **Validation System**: Comprehensive validation of YAML structure, required fields, and value types
- **Error Handling**: Clear, actionable error messages for configuration issues
- **Dependency Management**: Added PyYAML>=6.0.0 as a core dependency for YAML parsing

## [0.1.6] - 2025-09-27

### Added

- **Config Component Design Changes**: Updated configuration component architecture
- **Documentation Updates**: Enhanced and updated project documentation

### Changed

- **Config Component**: Refactored configuration component design
- **Documentation**: Updated documentation structure and content

### Fixed

- **Documentation Accuracy**: Fixed and improved documentation accuracy

## [0.1.5] - 2025-09-20

### Added

- **Complete Redis Storage Backend**: Implemented full Redis-based storage architecture
  - **RedisStorageManager**: Service layer for Redis storage lifecycle management
  - **RedisStorageClient**: Main client for Redis operations with connection pooling
  - **RedisStorageDict**: Storage abstraction implementing Prometheus multiprocess protocols
  - **RedisMultiProcessCollector**: Collector that aggregates metrics from Redis across processes
  - **RedisValue**: Redis-backed value implementation for individual metrics
- **Prometheus Specification Compliance**: Full support for all multiprocess modes
  - **Multiprocess Modes**: `all`, `liveall`, `live`, `max`, `min`, `sum`, `mostrecent`
  - **Per-Worker Metrics**: Worker metrics use `multiprocess_mode="all"` for individual worker visibility
  - **PID Labels**: All worker metrics include `pid` labels for process identification
- **Redis Key Architecture**: Structured key format with embedded process information
  - **Key Format**: `gunicorn:{metric_type}_{mode}:{pid}:{data_type}:{hash}`
  - **Hashed Keys**: Uses `hashlib.md5` for stable, deterministic key generation
  - **Metadata Storage**: Separate metadata storage for efficient querying
- **Performance Optimizations**:
  - **Batch Operations**: Groups Redis operations for efficiency
  - **Streaming Collection**: Processes metrics in batches to avoid memory overload
  - **Lock-Free Reads**: Uses Redis `scan_iter` for non-blocking key iteration
  - **Metadata Caching**: Reduces Redis lookups for frequently accessed metadata
- **System Testing Features**:
  - **Prometheus Metrics Verification**: Detailed metrics output after 15-second scraping wait
  - **Comprehensive Redis Integration**: Full Redis storage validation
  - **Signal Handling Testing**: Complete signal handling and metric capture validation
  - **TTL Configuration**: Redis key expiration verification
  - **Worker Restart Metrics Testing**: Comprehensive testing of worker restart metrics with QUIT/ABRT signals
  - **Enhanced Worker PID Detection**: Multiple fallback methods for finding worker processes in Docker
- **Core Implementation Features**:
  - **Lock-Free Operations**: Non-blocking Redis operations with per-key locking
  - **Robust Data Parsing**: Centralized bytes→str + float parsing utilities
  - **Unified TTL Management**: Single configuration gate for Redis key expiration
  - **Redis Server Time**: Coherent server-side timestamps using Redis time
  - **Memory-Efficient Cleanup**: Streaming cleanup operations to avoid memory overload
  - **Structured Key Architecture**: Embedded multiprocess modes in Redis key structure
  - **Method Signatures**: `read_value` and `write_value` with `multiprocess_mode` parameter
  - **RedisValue Integration**: Complete integration with Redis storage methods
  - **System Test Robustness**: Timeout handling and shell script reliability
  - **Code Formatting**: Comprehensive linting and formatting compliance
- **Complete Documentation Suite**:
  - **Backend Architecture Guide**: Complete architecture documentation (`docs/backend-architecture.md`)
  - **API Reference**: Detailed Redis backend API documentation
  - **Integration Examples**: Code examples for all Redis backend components
  - **Configuration Guide**: Complete Redis configuration options

### Changed

- **Architecture**: Replaced Redis forwarding with direct Redis storage backend
- **Worker Metrics**: Changed gauge metrics to use `multiprocess_mode="all"` for per-worker visibility
- **Key Structure**: Implemented structured Redis keys with embedded multiprocess modes
- **Documentation**: Updated all documentation to reflect current Redis storage implementation
- **System Tests**: Enhanced system tests with detailed Prometheus metrics verification
- **Request Object Extraction**: Refactored to use robust attribute-based detection instead of fragile positional arguments
- **Code Architecture**: Eliminated duplicate endpoint normalization logic with helper methods
- **Worker Implementation**: Unified all worker types to use consistent `_generic_handle_request` method

### Fixed

- **Worker Restart Metrics**: Fixed `gunicorn_worker_restart_total` and `gunicorn_worker_restart_count_total` metrics
  - Added proper imports for `WORKER_RESTART_REASON` and `WORKER_RESTART_COUNT`
  - Implemented worker restart tracking in `_generic_handle_quit` and `_generic_handle_abort` methods
  - Added comprehensive worker-specific signal testing (QUIT/ABRT) in system tests
- **Request Object Detection**: Improved robustness across different worker types and method signatures
- **Code Duplication**: Eliminated duplicate endpoint normalization logic with `_extract_request_info()` helper method
- **Return Value Handling**: Fixed return value propagation in signal handlers and request methods
- **Import Errors**: Resolved import issues after worker cleanup

### Technical Details

- **Redis Storage Format**: Metrics stored as Redis hashes with value, timestamp, and updated_at fields
- **Metadata Format**: Separate metadata storage with multiprocess_mode, metric_name, labelnames, help_text
- **Error Handling**: Graceful fallback to file-based storage if Redis unavailable
- **Connection Management**: Efficient Redis connection pooling and retry logic
- **Atomic Operations**: Thread-safe metric updates using Redis transactions
- **Process Isolation**: Each worker process maintains separate metric instances
- **Label Preservation**: All metric labels and metadata preserved in Redis storage
- **Robust Request Extraction**: Attribute-based request object detection using `hasattr()` checks
- **Unified Error Handling**: Consistent error metrics collection across all worker types

### Removed

- **Redis Forwarding References**: Removed all outdated Redis forwarding documentation and configuration
- **Outdated Architecture**: Removed references to old forwarding-based Redis integration
- **Request/Response Size Metrics**: Removed `gunicorn_worker_request_size_bytes` and `gunicorn_worker_response_size_bytes` metrics
- **Unused Methods**: Removed `_extract_request_size` and related unused methods

## [0.1.3] - 2025-07-28

### Added

- **Multi-Worker Type Support**: Added support for all major Gunicorn worker types:
  - `PrometheusThreadWorker`: Thread-based workers for I/O-bound applications
  - `PrometheusEventletWorker`: Eventlet-based workers for async I/O
  - `PrometheusGeventWorker`: Gevent-based workers for async I/O
- **Comprehensive Testing**: Added test applications and configurations for all worker types
- **Enhanced Documentation**: Updated all documentation to include new worker types
- **Improved Error Handling**: Better error handling and metrics collection for different worker signatures

### Changed

- **Documentation Updates**: Updated README, API reference, and framework integration guides
- **Configuration Examples**: Added worker type-specific configuration examples

### Fixed

- **Method Signature Issues**: Fixed `handle_request` method signatures for different worker types
- **Async Worker Compatibility**: Resolved compatibility issues with async workers
- **Master Process Tracking**: Ensured master metrics work correctly with all worker types

### Technical Details

- **Plugin Architecture**: Implemented `PrometheusMixin` for shared functionality across worker types
- **Conditional Imports**: Added proper conditional imports for optional worker dependencies
- **Test Coverage**: Comprehensive testing of all worker types with metrics validation

## [0.1.2] - 2025-07-27

### Added

- **Redis Forwarding**: Added Redis metrics forwarding capability
- **Comprehensive Documentation**: Full MkDocs documentation site
- **GitHub Actions**: Automated documentation deployment
- **Enhanced Configuration**: Improved configuration management system

### Changed

- **Documentation Structure**: Reorganized documentation with framework-agnostic approach
- **Example Configurations**: Updated example configurations for better clarity
- **Error Tracking**: Improved error tracking and reporting

## [0.1.1] - 2025-07-26

### Added

- **Master Process Metrics**: Added metrics for Gunicorn master process
- **Signal Handling**: Track worker restarts and signal handling
- **Multiprocess Support**: Full Prometheus multiprocess compatibility

### Fixed

- **Code Duplication**: Refactored Redis hook to reduce code duplication
- **Documentation Accuracy**: Fixed inaccurate documentation in examples
- **Environment Variables**: Improved environment variable handling

## [0.1.0] -

### Added

- **Initial Release**: Basic Prometheus metrics exporter for Gunicorn
- **Worker Metrics**: CPU, memory, request duration tracking
- **Basic Configuration**: Simple setup and configuration options
- **Framework Support**: Works with any WSGI framework (Django, FastAPI, Flask, etc.)
