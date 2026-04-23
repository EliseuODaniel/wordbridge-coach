#!/bin/bash

# WordBridge Coach Backend Test Runner
# Usage: ./test-runner.sh [test_type] [options]

set -e

echo "🧪 WordBridge Coach Backend Test Runner"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
SPEC4_ONLY=false
PYTHON_BIN="python"
PIP_BIN="pip"
PYTEST_CMD="python -m pytest"

if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
    PIP_BIN=".venv/bin/pip"
    PYTEST_CMD=".venv/bin/python -m pytest"
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --spec4)
            TEST_TYPE="spec4"
            SPEC4_ONLY=true
            shift
            ;;
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [test_type] [options]"
            echo ""
            echo "Test types:"
            echo "  --unit         Run unit tests only"
            echo "  --integration  Run integration tests only"
            echo "  --spec4        Run Spec4 specific tests only"
            echo "  --all          Run all tests (default)"
            echo ""
            echo "Options:"
            echo "  --coverage     Generate coverage report"
            echo "  --verbose      Verbose output"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    if [[ "$PYTHON_BIN" == ".venv/bin/python" ]]; then
        echo "Using repo-local test environment at .venv/"
    else
        echo "Consider activating venv first: source .venv/bin/activate"
    fi
    echo ""
fi

# Check if test dependencies are installed
echo -e "${BLUE}Checking test dependencies...${NC}"
if ! "$PYTHON_BIN" -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    "$PIP_BIN" install -r requirements-test.txt
fi

# Create test database if needed
echo -e "${BLUE}Setting up test environment...${NC}"

REPO_ROOT="$(cd .. && pwd)"
TMPDIR="${TMPDIR:-$REPO_ROOT/.tmp_pytest}"
mkdir -p "$TMPDIR"
export TMPDIR

# Check if test database is available
echo -e "${BLUE}Checking test database connectivity...${NC}"
if ! "$PYTHON_BIN" -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test')
    conn.close()
    print('Test database is accessible')
except Exception as e:
    print(f'Test database not accessible: {e}')
    print('Please run: docker compose --profile test up -d db_test')
    exit(1)
" 2>/dev/null; then
    echo -e "${RED}❌ Test database not accessible. Please start the test database:${NC}"
    echo -e "${YELLOW}docker compose --profile test up -d db_test${NC}"
    exit 1
fi

# Build pytest command
PYTEST_ENV_PREFIX="PYTHONPATH=. DEBUG=false TMPDIR=$TMPDIR"

if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term-missing"
fi

# Set test directory based on type
case $TEST_TYPE in
    unit)
        TEST_DIR="tests/unit"
        ;;
    integration)
        TEST_DIR="tests/integration"
        ;;
    spec4)
        TEST_DIR="tests/integration -m spec4"
        ;;
    all)
        TEST_DIR="tests"
        ;;
esac

# Run tests
echo -e "${BLUE}Running tests: $TEST_TYPE${NC}"
echo -e "${BLUE}Command: $PYTEST_ENV_PREFIX $PYTEST_CMD $TEST_DIR${NC}"
echo ""

# Execute tests
if eval "$PYTEST_ENV_PREFIX $PYTEST_CMD $TEST_DIR"; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"

    if [[ "$COVERAGE" == true ]]; then
        echo -e "${BLUE}📊 Coverage report generated in htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

# Show test results summary
echo ""
echo -e "${BLUE}Test Summary:${NC}"
echo "- Test Type: $TEST_TYPE"
echo "- Coverage: $COVERAGE"
echo "- Verbose: $VERBOSE"

if [[ "$SPEC4_ONLY" == true ]]; then
    echo "- Spec4 Tests Only: Yes"
fi

echo ""
echo -e "${GREEN}🎉 Test run completed successfully!${NC}"
