import pytest
from config.settings import settings
from graphs.orchestration import compile_graph

def test_graph_compilation():
    """Verify that the orchestration graph compiles successfully with the Postgres checkpointer."""
    try:
        graph = compile_graph()
        assert graph is not None
        # Verify the structure has our nodes registered
        node_names = list(graph.nodes.keys())
        assert "planner" in node_names
        assert "supervisor" in node_names
        assert "research" in node_names
        assert "retriever" in node_names
        assert "memory" in node_names
        assert "verification" in node_names
        assert "reflection" in node_names
    except Exception as e:
        pytest.fail(f"Graph compilation failed: {e}")
