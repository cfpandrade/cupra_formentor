# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2025-05-25

### 🎉 Major Update

### Added
- Support for official WeConnect library (stable and maintained)
- Better hybrid vehicle compatibility
- Enhanced error handling and logging
- Formentor-specific service names
- Improved authentication flow

### Changed
- **BREAKING**: Updated from `weconnect-cupra-daern` to official `weconnect` library
- Service names updated from `volkswagen_id_*` to `cupra_formentor_*`
- Entity naming improved for Cupra branding
- Enhanced handling of None values for hybrid vehicles

### Fixed
- Library import issues and crashes
- Authentication throttling handling
- Hybrid vehicle charging status display
- Missing dependencies and imports

### Removed
- Dependency on problematic `weconnect-cupra-daern` fork
- Unnecessary `ascii_magic` dependency
- VW-specific branding and references

## [0.1.0] - Initial Release

### Added
- Initial Cupra Formentor integration
- Basic sensor support
- Charging and climate control
- Device tracking
- HACS compatibility
