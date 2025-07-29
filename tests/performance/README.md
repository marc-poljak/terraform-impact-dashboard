# Performance Tests

This directory contains comprehensive performance tests for the Terraform Plan Impact Dashboard to ensure it meets the performance requirements specified in the project requirements.

## Test Coverage

### 1. Large File Processing Tests (`test_large_files.py`)

Tests file processing performance to ensure compliance with the requirement that large plan files complete processing within 10 seconds.

**Test Cases:**
- Small file processing (< 1 second)
- Medium file processing (100 resources, < 3 seconds)
- Large file processing (500 resources, < 10 seconds)
- Very large file processing (1000 resources, < 10 seconds)
- Memory usage monitoring
- Caching performance validation
- Chunked processing verification
- Concurrent processing safety
- File size scaling analysis

### 2. Filter Performance Tests (`test_filter_performance.py`)

Tests filtering operations to ensure compliance with the requirement that filter results update within 2 seconds.

**Test Cases:**
- Action filtering performance
- Risk level filtering performance
- Provider filtering performance
- Text search functionality performance
- Combined filter operations
- Large dataset filtering (up to 5000 resources)
- Filter caching effectiveness
- Memory efficiency during filtering
- Concurrent filter operations
- Filter performance scalability

### 3. Memory Usage Tests (`test_memory_usage.py`)

Tests memory usage patterns and resource cleanup to prevent memory leaks during long-running sessions.

**Test Cases:**
- Single file processing memory usage
- Multiple file processing memory patterns
- Caching system memory impact
- Concurrent processing memory usage
- Long-running session simulation
- Memory scaling with file size
- Garbage collection effectiveness
- Resource cleanup verification

### 4. Performance Benchmarks (`test_performance_benchmarks.py`)

Comprehensive benchmarking suite that establishes performance baselines and detects regressions.

**Features:**
- Automated benchmark execution
- Performance threshold validation
- Regression detection
- Comprehensive reporting
- Benchmark result persistence
- Category-based performance analysis

## Performance Requirements

The tests validate the following performance requirements from the project specification:

1. **Large File Processing**: Files with many resources must complete processing within 10 seconds
2. **Filter Response Time**: Filter operations must complete within 2 seconds
3. **Memory Efficiency**: Memory usage must remain reasonable and not leak over time
4. **Concurrent Safety**: Operations must work correctly under concurrent access

## Running the Tests

### Run All Performance Tests
```bash
python -m pytest tests/performance/ -v
```

### Run Specific Test Categories
```bash
# Large file processing tests
python -m pytest tests/performance/test_large_files.py -v

# Filter performance tests
python -m pytest tests/performance/test_filter_performance.py -v

# Memory usage tests
python -m pytest tests/performance/test_memory_usage.py -v

# Benchmark suite
python -m pytest tests/performance/test_performance_benchmarks.py -v
```

### Run Quick Performance Check
```bash
python -m pytest tests/performance/ -v -k "test_small_file_processing_performance or test_action_filter_performance"
```

## Dependencies

The performance tests require the following additional dependencies:
- `psutil>=5.9.0` - For memory and process monitoring
- `pytest>=7.0.0` - Test framework
- `pandas>=1.5.0` - Data processing
- Standard library modules: `time`, `gc`, `threading`, `statistics`

## Test Data Generation

The tests include sophisticated test data generators that create realistic Terraform plans with:
- Multiple cloud providers (AWS, Azure, GCP)
- Various resource types and configurations
- Different complexity levels (simple, medium, complex)
- Configurable resource counts for scalability testing
- Realistic resource relationships and dependencies

## Performance Monitoring

The tests include built-in performance monitoring that tracks:
- Execution time for all operations
- Memory usage patterns
- Cache hit/miss ratios
- Resource cleanup effectiveness
- Concurrent operation safety

## Threshold Configuration

Performance thresholds are configurable and based on the project requirements:
- Large file processing: 10 seconds maximum
- Filter operations: 2 seconds maximum
- Memory usage: Reasonable limits with leak detection
- Cache effectiveness: Minimum improvement ratios

## Reporting

The benchmark suite generates comprehensive reports including:
- Performance statistics and trends
- Threshold violation alerts
- Category-based analysis
- Detailed operation metrics
- Regression detection results

Reports can be saved to JSON files for historical analysis and CI/CD integration.