# Changelog

All notable changes to this project will be documented in this file.

## [0.1.3] - 2025-07-28

### Added
- **Multi-Worker Type Support**: Added support for all major Gunicorn worker types:
  - `PrometheusThreadWorker`: Thread-based workers for I/O-bound applications
  - `PrometheusEventletWorker`: Eventlet-based workers for async I/O
  - `PrometheusGeventWorker`: Gevent-based workers for async I/O
  - `PrometheusTornadoWorker`: Tornado-based workers for async applications
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
