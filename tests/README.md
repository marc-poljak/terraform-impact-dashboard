# Test Suite for Terraform Plan Impact Dashboard

This directory contains the test suite for the dashboard components, organized into unit, integration, and performance tests.

## Test Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── test_components_basic.py    # Basic functionality tests for all components
│   ├── test_header_component.py    # Detailed HeaderComponent tests
│   ├── test_sidebar_component.py   # Detailed SidebarComponent tests
│   ├── test_upload_component.py    # Detailed UploadComponent tests
│   └── test_session_manager.py     # SessionStateManager tests
├── integration/                    # Integration tests (future)
├── performance/                    # Performance tests (future)
└── README.md                       # This file
```

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Basic component tests (recommended for CI)
python -m pytest tests/unit/test_components_basic.py -v

# Specific component tests
python -m pytest tests/unit/test_header_component.py -v
```

### Test Options
```bash
# Verbose output
python -m pytest tests/unit/ -v

# Stop on first failure
python -m pytest tests/unit/ -x

# Show detailed output for failures
python -m pytest tests/unit/ -vv
```

## Test Coverage

### HeaderComponent ✅
- **Creation**: Component instantiation
- **Methods**: `render()` and `render_css()` method existence and functionality
- **Output**: Proper HTML/CSS content generation
- **Styling**: Multi-cloud provider CSS classes and styling preservation

### UploadComponent ✅
- **Creation**: Component instantiation
- **Methods**: All required methods (`render`, `validate_and_parse_file`, etc.)
- **Validation**: Plan structure validation with various data formats
- **Error Handling**: Invalid JSON and missing field handling
- **File Processing**: Minimal structure requirements

### SidebarComponent ✅
- **Creation**: Component instantiation with SessionStateManager
- **Methods**: All required methods (`render`, `render_filters`, etc.)
- **Filters**: Preset filter configurations
- **Validation**: Filter expression validation and parsing
- **State Management**: Integration with SessionStateManager

### SessionStateManager ✅
- **Import**: Module can be imported successfully
- **Creation**: Component instantiation with mocked Streamlit session state
- **Basic Functionality**: Core session state management capabilities

## Test Philosophy

The test suite follows these principles:

1. **Minimal Mocking**: Tests use minimal mocking to focus on actual functionality
2. **Isolation**: Each test is independent and doesn't rely on external state
3. **Regression Prevention**: Tests verify that existing functionality is preserved
4. **Component Contracts**: Tests verify that components have expected methods and interfaces

## Mock Strategy

- **Streamlit Dependencies**: Mocked to avoid requiring Streamlit runtime
- **Session State**: Custom mock class that supports both dict and attribute access
- **External Dependencies**: Mocked only when necessary for test isolation

## Test Data

Tests use realistic mock data that represents:
- Valid Terraform plan JSON structures
- Various error conditions and edge cases
- Different component states and configurations

## Future Enhancements

### Integration Tests (Planned)
- Component interaction testing
- End-to-end workflow validation
- Data flow between components

### Performance Tests (Planned)
- Large file processing performance
- Memory usage validation
- Response time benchmarks

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Streamlit Warnings**: Normal when running tests outside Streamlit runtime
3. **Mock Failures**: Check that mocks match actual component interfaces

### Debug Mode
```bash
# Run with debug output
python -m pytest tests/unit/ -v -s

# Run specific test with full output
python -m pytest tests/unit/test_components_basic.py::TestHeaderComponent::test_component_creation -vv
```

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Use minimal mocking approach
3. Test both success and failure cases
4. Include docstrings explaining test purpose
5. Ensure tests are independent and can run in any order