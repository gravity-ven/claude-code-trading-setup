# Spartan Research Station - Testing Guide

**Enterprise-Grade Testing Strategy**
**Unit → Integration → Load → Security → End-to-End**

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Continuous Integration](#continuous-integration)
6. [Performance Benchmarks](#performance-benchmarks)

---

## Testing Overview

### Testing Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│               SPARTAN TESTING PYRAMID                       │
│                                                             │
│                    E2E Tests (5%)                          │
│                  /              \                           │
│            Integration Tests (20%)                          │
│          /                          \                       │
│      Load/Security Tests (25%)                              │
│    /                                  \                     │
│                Unit Tests (50%)                             │
└─────────────────────────────────────────────────────────────┘
```

### Success Criteria

- ✅ **Unit Tests**: 85%+ coverage, 95%+ pass rate
- ✅ **Integration Tests**: 100% API endpoint coverage, 95%+ pass rate
- ✅ **Load Tests**: 1000+ concurrent users, <200ms p95 response time
- ✅ **Security Tests**: Zero critical vulnerabilities
- ✅ **End-to-End Tests**: 100% user workflow coverage

---

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test individual functions and classes in isolation

**Coverage**:
- Data fetchers (Yahoo, FRED, Polygon, etc.)
- Database managers (insert, query, update)
- Cache managers (Redis operations)
- API route handlers
- Utility functions

**Example**:
```python
# tests/unit/test_yahoo_fetcher.py
import pytest
from src.preloader.main import YahooFinanceFetcher

def test_yahoo_fetch_quotes():
    fetcher = YahooFinanceFetcher()
    data = fetcher.fetch_quotes(['AAPL', 'MSFT'])

    assert len(data) == 2
    assert 'symbol' in data[0]
    assert 'price' in data[0]
    assert data[0]['symbol'] in ['AAPL', 'MSFT']
```

**Run unit tests**:
```bash
pytest tests/unit/ -v --cov=src --cov-report=html
```

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test interactions between components

**Coverage**:
- API endpoint integration with database
- Pre-loader → PostgreSQL data flow
- Refresh service → Database updates
- Cache invalidation logic
- Multi-source fallback chains

**Example**:
```python
# tests/integration/test_api_endpoints.py
import pytest
from src.web.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_market_indices_endpoint(client):
    response = client.get('/api/market/indices')

    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert len(data['data']) > 0
    assert 'source' in data
    assert data['source'] == 'database'
```

**Run integration tests**:
```bash
pytest tests/integration/ -v
```

### 3. Load Tests (`tests/load/`)

**Purpose**: Test system performance under heavy load

**Coverage**:
- Concurrent API requests
- Database connection pool limits
- Redis cache performance
- Response time percentiles (p50, p95, p99)

**Tools**: Locust, Apache Bench

**Example (Locust)**:
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class SpartanUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_market_indices(self):
        self.client.get("/api/market/indices")

    @task(2)
    def get_commodities(self):
        self.client.get("/api/market/commodities")

    @task(1)
    def get_correlations(self):
        self.client.get("/api/analytics/correlations")
```

**Run load tests**:
```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host http://localhost:8888 --users 1000 --spawn-rate 10
```

**Benchmarks**:
- **Target RPS**: 500+ requests/second
- **Target p95**: <200ms response time
- **Target p99**: <500ms response time
- **Max users**: 1000+ concurrent

### 4. Security Tests (`tests/security/`)

**Purpose**: Identify security vulnerabilities

**Coverage**:
- SQL injection prevention
- XSS protection
- CSRF protection
- Authentication/authorization
- API rate limiting
- Dependency vulnerabilities

**Tools**: Bandit, Safety, OWASP ZAP

**Run security tests**:
```bash
# Python security linter
bandit -r src/ -f json -o tests/security/bandit_report.json

# Dependency vulnerability scan
safety check --json > tests/security/safety_report.json

# OWASP ZAP scan (requires ZAP running)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8888 \
  -J tests/security/zap_report.json
```

**Success Criteria**:
- Zero critical vulnerabilities
- Zero high vulnerabilities
- <5 medium vulnerabilities (all documented)

### 5. End-to-End Tests (`tests/e2e/`)

**Purpose**: Test complete user workflows

**Coverage**:
- Dashboard load and display
- Flashcard navigation
- Symbol search
- Chart rendering
- Data refresh cycles

**Tools**: Selenium, Playwright

**Example (Selenium)**:
```python
# tests/e2e/test_dashboard.py
from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

def test_dashboard_loads(driver):
    driver.get("http://localhost:8888")

    # Check title
    assert "Spartan Research Station" in driver.title

    # Check logo displays
    logo = driver.find_element(By.CLASS_NAME, "spartan-logo")
    assert logo.is_displayed()

    # Check flashcards load
    flashcards = driver.find_elements(By.CLASS_NAME, "flashcard")
    assert len(flashcards) > 0
```

**Run e2e tests**:
```bash
pytest tests/e2e/ -v --browser=chrome
```

---

## Running Tests

### Quick Test Commands

```bash
# Run ALL tests
pytest tests/ -v

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run in parallel (faster)
pytest tests/ -v -n auto

# Run only failed tests
pytest --lf

# Run specific test file
pytest tests/unit/test_yahoo_fetcher.py -v

# Run specific test function
pytest tests/unit/test_yahoo_fetcher.py::test_yahoo_fetch_quotes -v
```

### Full Test Suite (Enterprise)

```bash
# Run complete enterprise test suite
bash tests/run_enterprise_tests.sh
```

This script runs:
1. Unit tests with coverage
2. Integration tests
3. Load tests (5 minutes)
4. Security scans
5. E2E tests
6. Generates comprehensive report

**Expected Duration**: 15-30 minutes

---

## Test Coverage

### Current Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| Data Fetchers | 85% | TBD |
| Database Managers | 90% | TBD |
| API Endpoints | 100% | TBD |
| Pre-Loader | 80% | TBD |
| Refresh Service | 80% | TBD |
| Web Server | 85% | TBD |
| **Overall** | **85%** | **TBD** |

### Generate Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Open report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Analysis

```bash
# Show missing lines
pytest tests/ --cov=src --cov-report=term-missing

# Coverage by file
pytest tests/ --cov=src --cov-report=term

# Fail if coverage below threshold
pytest tests/ --cov=src --cov-fail-under=85
```

---

## Continuous Integration

### GitHub Actions Workflow

`.github/workflows/test.yml`:

```yaml
name: Spartan Research Station Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: timescale/timescaledb:latest-pg15
        env:
          POSTGRES_DB: spartan_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Run security scans
        run: |
          pip install bandit safety
          bandit -r src/
          safety check

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-Commit Hooks

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: unit-tests
        name: Run unit tests
        entry: pytest tests/unit/ -v
        language: system
        pass_filenames: false
        always_run: true

      - id: security-scan
        name: Security scan
        entry: bandit -r src/
        language: system
        pass_filenames: false
        always_run: true
```

Install pre-commit:
```bash
pip install pre-commit
pre-commit install
```

---

## Performance Benchmarks

### Database Performance

**Query Performance Targets**:

| Query Type | Target | Benchmark |
|------------|--------|-----------|
| Single symbol | <10ms | TBD |
| 100 symbols | <50ms | TBD |
| Correlations (1000 pairs) | <200ms | TBD |
| Full table scan | <1s | TBD |

**Benchmark script**:
```bash
python tests/benchmarks/test_db_performance.py
```

### API Performance

**Endpoint Response Time Targets**:

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| /api/market/indices | <50ms | <100ms | <200ms |
| /api/market/commodities | <50ms | <100ms | <200ms |
| /api/analytics/correlations | <100ms | <200ms | <500ms |
| /api/db/search | <30ms | <80ms | <150ms |

**Benchmark script**:
```bash
python tests/benchmarks/test_api_performance.py
```

### Cache Performance

**Redis Cache Targets**:

- **Hit rate**: >90%
- **Get latency**: <1ms
- **Set latency**: <2ms
- **Memory usage**: <4GB

**Benchmark script**:
```bash
python tests/benchmarks/test_cache_performance.py
```

---

## Test Data

### Test Database Setup

```bash
# Create test database
docker exec spartan_postgres createdb -U spartan_user spartan_test

# Load test data
docker exec -i spartan_postgres psql -U spartan_user -d spartan_test < tests/fixtures/test_data.sql
```

### Test Fixtures

Located in `tests/fixtures/`:

- `test_data.sql` - Sample market data (1000 rows)
- `mock_api_responses.json` - Mock API responses for unit tests
- `sample_symbols.json` - Test symbol list

### Mock Data Guidelines

**Unit tests**: Use mocks for external API calls
```python
import pytest
from unittest.mock import patch

@patch('yfinance.download')
def test_yahoo_fetcher(mock_download):
    mock_download.return_value = mock_dataframe
    # Test logic here
```

**Integration tests**: Use test database with real schema, sample data

**E2E tests**: Use staging environment with full data

---

## Debugging Failed Tests

### Common Issues

**1. Database connection failures**:
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check database exists
docker exec spartan_postgres psql -U spartan_user -l
```

**2. Redis connection failures**:
```bash
# Check Redis is running
docker exec spartan_redis redis-cli ping
```

**3. API key errors**:
```bash
# Verify .env file
cat .env | grep API_KEY
```

**4. Import errors**:
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$PWD:$PYTHONPATH
```

### Debug Mode

```bash
# Run tests with verbose output
pytest tests/ -vv

# Show print statements
pytest tests/ -s

# Drop into debugger on failure
pytest tests/ --pdb

# Show slowest tests
pytest tests/ --durations=10
```

---

## Test Reports

### Generate Test Reports

```bash
# HTML report
pytest tests/ --html=reports/test_report.html --self-contained-html

# JUnit XML (for CI)
pytest tests/ --junitxml=reports/junit.xml

# Coverage report
pytest tests/ --cov=src --cov-report=html:reports/coverage

# Combined report
pytest tests/ \
  --html=reports/test_report.html \
  --junitxml=reports/junit.xml \
  --cov=src \
  --cov-report=html:reports/coverage
```

### View Reports

```bash
# Open test report
open reports/test_report.html

# Open coverage report
open reports/coverage/index.html
```

---

## Best Practices

### Writing Good Tests

✅ **DO**:
- Write tests before or alongside code (TDD)
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests independent and isolated
- Use fixtures for common setup
- Mock external dependencies

❌ **DON'T**:
- Test implementation details
- Write tests dependent on execution order
- Use sleep() for timing (use proper async/await)
- Leave commented-out test code
- Skip tests without explanation

### Test Naming Convention

```python
# Pattern: test_<function_name>_<scenario>_<expected_outcome>

def test_fetch_quotes_valid_symbols_returns_data():
    """Test that fetch_quotes returns data for valid symbols"""
    pass

def test_fetch_quotes_invalid_symbol_returns_empty():
    """Test that fetch_quotes returns empty for invalid symbols"""
    pass

def test_fetch_quotes_network_error_raises_exception():
    """Test that fetch_quotes raises exception on network error"""
    pass
```

---

## Conclusion

**Testing Checklist**:

- [ ] All unit tests passing (85%+ coverage)
- [ ] All integration tests passing
- [ ] Load tests meeting performance targets
- [ ] Zero critical security vulnerabilities
- [ ] E2E tests covering all user workflows
- [ ] CI/CD pipeline configured
- [ ] Test reports generated
- [ ] Performance benchmarks documented

**Next Steps**:
1. Run full test suite: `bash tests/run_enterprise_tests.sh`
2. Review test coverage report
3. Fix any failing tests
4. Address security vulnerabilities
5. Optimize slow tests
6. Deploy to staging for final validation

---

**Last Updated**: November 19, 2025
**Test Framework**: pytest
**Coverage Target**: 85%
**Status**: Enterprise-Ready
