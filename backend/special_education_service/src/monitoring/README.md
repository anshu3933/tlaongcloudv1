# Monitoring System

This monitoring system provides comprehensive observability for the Special Education Service, specifically designed to track version conflicts and system health that were critical issues in the IEP management system.

## Overview

The monitoring system consists of several components working together to provide real-time insights into system performance and conflicts:

### 🎯 **Core Components**

1. **MetricsCollector** (`metrics_collector.py`)
   - Collects and aggregates performance metrics
   - Tracks version conflicts with detailed context
   - Stores metrics in memory with configurable retention
   - Provides summary statistics and alerts

2. **HealthMonitor** (`health_monitor.py`) 
   - Monitors system resources (CPU, memory, disk)
   - Tracks database connectivity and performance
   - Runs background health checks every 30 seconds
   - Generates alerts for degraded performance

3. **MonitoringMiddleware** (`middleware.py`)
   - Automatically tracks all API requests
   - Records performance metrics for each operation
   - Detects and logs version conflicts
   - Provides decorators for custom tracking

4. **MonitoringRouter** (`monitoring_router.py`)
   - Exposes metrics via REST API endpoints
   - Serves interactive monitoring dashboard
   - Provides health check endpoints

## Key Features

### ✅ **Version Conflict Tracking**
- **Conflict Detection**: Automatically detects IEP version conflicts
- **Resolution Tracking**: Monitors retry attempts and resolution time
- **Student Context**: Tracks which students are most affected
- **Conflict Types**: Categorizes conflicts (version_conflict, retry_exhausted, database_error)

### ✅ **Performance Monitoring**  
- **Response Times**: Tracks average, 95th percentile response times
- **Success Rates**: Monitors operation success/failure rates
- **Throughput**: Tracks operations per minute
- **Slow Operations**: Identifies and logs operations >1 second

### ✅ **System Health**
- **Resource Usage**: CPU, memory, disk utilization
- **Database Health**: Connection status and response times
- **Application Metrics**: Active sessions, pending operations
- **Automated Alerts**: Warnings for degraded performance

### ✅ **Real-time Dashboard**
- **Visual Interface**: HTML dashboard with auto-refresh
- **Live Metrics**: Updates every 30 seconds
- **Alert Display**: Shows active system alerts
- **Historical Data**: Hourly statistics and trends

## API Endpoints

### Core Monitoring
```
GET /monitoring/dashboard          # Interactive HTML dashboard
GET /monitoring/health             # Comprehensive health status
GET /monitoring/metrics            # Complete metrics dashboard data
GET /monitoring/alerts             # Current system alerts
```

### Specific Metrics
```
GET /monitoring/metrics/conflicts?hours=24    # Version conflict metrics
GET /monitoring/metrics/performance?hours=24  # Performance metrics  
GET /monitoring/database/health              # Database connectivity
GET /monitoring/status                       # Monitoring system status
```

### Detailed Views
```
GET /monitoring/conflicts/recent?limit=10     # Recent conflict events
GET /monitoring/performance/slowest?limit=10  # Slowest operations
GET /monitoring/summary/hourly               # Hourly statistics
```

### Maintenance
```
POST /monitoring/cleanup                     # Cleanup old data
```

## Usage Examples

### Accessing the Dashboard
```bash
# Open monitoring dashboard in browser
curl http://localhost:8005/monitoring/dashboard

# Or visit directly:
# http://localhost:8005/monitoring/dashboard
```

### Getting Health Status
```bash
# Quick health check
curl http://localhost:8005/monitoring/health/simple

# Comprehensive health data
curl http://localhost:8005/monitoring/health
```

### Monitoring Version Conflicts
```bash
# Get conflict summary for last 24 hours
curl "http://localhost:8005/monitoring/metrics/conflicts?hours=24"

# Get recent conflict events
curl "http://localhost:8005/monitoring/conflicts/recent?limit=5"
```

### Performance Analysis
```bash
# Get performance metrics
curl "http://localhost:8005/monitoring/metrics/performance?hours=1"

# Find slowest operations
curl "http://localhost:8005/monitoring/performance/slowest?limit=10"
```

## Integration with Development Tools

### Dev Tools Commands
```bash
# View monitoring dashboard
./dev-tools.sh up
# Then visit: http://localhost:8006/monitoring/dashboard

# Check system health
curl http://localhost:8006/monitoring/health/simple

# Get current alerts
curl http://localhost:8006/monitoring/alerts
```

### Automated Monitoring in Tests
The monitoring system integrates with the test suite to track performance during integration tests:

```python
# Tests automatically track conflicts and performance
./dev-tools.sh test-concurrent
./dev-tools.sh test-performance
```

## Configuration

### Environment Variables
```bash
# Health check interval (seconds)
HEALTH_CHECK_INTERVAL=30

# Metrics retention (hours)  
METRICS_RETENTION_HOURS=24

# Maximum events to store in memory
MAX_METRICS_EVENTS=1000
```

### Auto-start Setup
The monitoring system starts automatically with the application:

```python
# In main.py lifespan manager
await health_monitor.start()  # Starts background monitoring
```

## Alert Thresholds

### Performance Alerts
- **High Error Rate**: >5% error rate triggers warning
- **Slow Response**: >1000ms average response time triggers warning  
- **Database Issues**: Connection failures trigger critical alert

### Resource Alerts
- **High CPU**: >80% CPU usage triggers warning
- **High Memory**: >85% memory usage triggers warning
- **Database Pool**: >90% pool utilization triggers warning

### Conflict Alerts
- **High Conflict Rate**: >10 conflicts/hour triggers warning
- **Retry Exhaustion**: Failed retries trigger conflict tracking

## Dashboard Features

### Real-time Updates
- **Auto-refresh**: Updates every 30 seconds
- **Manual Refresh**: Click refresh button for immediate update
- **Pause on Hidden**: Stops updates when browser tab is hidden

### Visual Status Indicators
- **Green**: Healthy system status
- **Yellow**: Degraded performance warnings  
- **Red**: Critical issues requiring attention
- **Gray**: Unknown or unavailable status

### Key Metrics Displayed
1. **System Health**: Overall status, database, memory, sessions
2. **Performance**: Operations, success rate, response times
3. **Version Conflicts**: Conflict count, rate, resolution time
4. **Active Alerts**: Current system alerts with severity

## Data Retention

### Memory Storage
- **Conflict Events**: Up to 1000 events (configurable)
- **Performance Metrics**: Up to 2000 metrics (configurable)
- **Health Snapshots**: Up to 100 snapshots (configurable)

### Automatic Cleanup
- **Retention Period**: 24 hours by default
- **Cleanup Frequency**: Every health check cycle (30 seconds)
- **Manual Cleanup**: Via `/monitoring/cleanup` endpoint

## Troubleshooting

### Common Issues

1. **Dashboard Not Loading**
   ```bash
   # Check if monitoring router is included
   curl http://localhost:8005/monitoring/status
   ```

2. **No Metrics Data**
   ```bash
   # Verify middleware is active
   curl http://localhost:8005/api/v1/students
   curl http://localhost:8005/monitoring/metrics
   ```

3. **Health Monitor Not Running**
   ```bash
   # Check monitoring status
   curl http://localhost:8005/monitoring/status
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check monitoring logs
./dev-tools.sh logs | grep -i monitoring
```

## Integration with Original Problem

This monitoring system directly addresses the original IEP version conflict issues:

### **Before**: Version conflicts caused system failures
- No visibility into conflict frequency
- No tracking of resolution success/failure  
- No performance impact measurement

### **After**: Comprehensive conflict monitoring
- ✅ Real-time conflict detection and tracking
- ✅ Retry mechanism performance measurement
- ✅ Student-specific conflict analysis
- ✅ Resolution time and success rate monitoring
- ✅ Automated alerts for degraded performance

### **Key Metrics for Version Conflicts**
- **Conflict Rate**: How often conflicts occur
- **Retry Success**: How often retries resolve conflicts
- **Resolution Time**: How long conflicts take to resolve
- **Affected Students**: Which students experience most conflicts
- **Performance Impact**: How conflicts affect overall system performance

This monitoring system ensures that the version conflict fixes are working correctly and provides early warning if issues resurface.