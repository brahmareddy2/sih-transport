import pytest
from app.main import app
from app.core.dependencies import get_current_user

@pytest.fixture(scope="module", autouse=True)
def auto_override_current_user_module(request):
    """
    Module-scoped fixture to ensure the dependency override is set
    before any module-level setups (like seed_test_database) run.
    """
    module = request.module
    mock_func = getattr(module, "mock_get_current_user", None)
    
    if not mock_func:
        # Fallback to checking variable names
        for var_name in ["mock_admin", "mock_user", "_mock_admin"]:
            user_obj = getattr(module, var_name, None)
            if user_obj:
                mock_func = lambda: user_obj
                break

    if mock_func:
        app.dependency_overrides[get_current_user] = mock_func
    else:
        app.dependency_overrides.pop(get_current_user, None)

    yield

    # Clean up after all tests in the module complete
    app.dependency_overrides.pop(get_current_user, None)
