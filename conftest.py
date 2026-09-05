"""
Transactra — Root conftest.py

Shared fixtures for all test suites.
Configures PYTHONPATH and provides common test utilities.
"""

from __future__ import annotations

import sys
import os
from uuid import uuid4

import pytest

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture
def random_uuid():
    """Generate a fresh UUID for test isolation."""
    return uuid4()


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_agent_id():
    return uuid4()


@pytest.fixture
def sample_merchant_id():
    return uuid4()


@pytest.fixture
def sample_mandate_id():
    return uuid4()


@pytest.fixture
def sample_cart_hash():
    return "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
