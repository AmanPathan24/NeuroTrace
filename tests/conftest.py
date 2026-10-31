"""Pytest session configuration and fixtures for NeuroTrace."""
import gc
import pytest


@pytest.fixture(autouse=True)
def cleanup_memory_after_test():
    """Run garbage collection after every test to release NIfTI and tensor buffers."""
    yield
    gc.collect()
