import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api.server import app, SimpleRateLimiter
from brain.agentic.world import WorldModel
from router import Router


@pytest.fixture
def clean_world():
    world = WorldModel()
    world.nodes.clear()
    world.graph.clear()
    self_edges = getattr(world, "edges", {})
    self_edges.clear()
    return world


def test_graph_nodes_and_edges(clean_world):
    """Verify nodes and edges addition, retrieval, and deletion."""
    clean_world.add_node("n1", "Project", {"name": "Coding Assistant", "importance": "High"})
    clean_world.add_node("n2", "Habit", {"name": "Write clean code", "frequency": "daily"})
    clean_world.add_edge("n1", "n2", "requires_habit")

    assert "n1" in clean_world.nodes
    assert "n2" in clean_world.nodes
    assert "n2" in clean_world.graph["n1"]
    assert "n1" in clean_world.graph["n2"]

    # Verify edge label
    key = "n1-n2"
    assert clean_world.edges[key] == "requires_habit"

    # Delete node
    clean_world.delete_node("n2")
    assert "n2" not in clean_world.nodes
    assert "n2" not in clean_world.graph["n1"]
    assert key not in clean_world.edges


def test_semantic_search(clean_world):
    """Verify semantic search queries match keywords and description."""
    clean_world.add_node("n1", "Goal", {"name": "Crack UPSC exam", "description": "Indian civil services study"})
    clean_world.add_node("n2", "Project", {"name": "Khushi web app", "description": "local python uvicorn"})

    results = clean_world.semantic_search("upsc civil")
    assert len(results) >= 1
    assert results[0]["id"] == "n1"

    results_app = clean_world.semantic_search("uvicorn local")
    assert len(results_app) >= 1
    assert results_app[0]["id"] == "n2"


def test_memory_merging_and_conflicts(clean_world):
    """Verify memory merging clashing values detection."""
    # 1. Merge new node
    nid1 = clean_world.merge_memory("personal", "location", {"value": "London"})
    assert nid1 in clean_world.nodes
    assert clean_world.nodes[nid1]["metadata"]["value"] == "London"

    # 2. Merge same node update (no duplicates)
    nid2 = clean_world.merge_memory("personal", "location", {"value": "London", "updated": True})
    assert nid1 == nid2
    assert clean_world.nodes[nid1]["metadata"]["updated"] is True

    # 3. Check conflict detection
    conflict = clean_world.check_conflict("personal", "location", "Paris")
    assert conflict is not None
    assert conflict["existing_value"] == "London"
    assert conflict["new_value"] == "Paris"


def test_explain_relationships(clean_world):
    """Verify human readable connection sentences generation."""
    clean_world.add_node("u1", "User", {"name": "Faisal"})
    clean_world.add_node("pl1", "Place", {"name": "New Delhi"})
    clean_world.add_node("p1", "Project", {"name": "UPSC prep"})
    clean_world.add_edge("u1", "pl1", "lives in")
    clean_world.add_edge("u1", "p1", "is preparing for")

    explanation = clean_world.explain_relationship("faisal")
    assert "lives in 'New Delhi'" in explanation
    assert "is preparing for 'UPSC prep'" in explanation


@pytest.fixture
def mock_brain():
    brain = MagicMock()
    world = WorldModel()
    # Seed mock brain with a test graph
    world.nodes.clear()
    world.graph.clear()
    world.edges.clear()
    
    world.add_node("u1", "User", {"name": "Faisal"})
    world.add_node("pl1", "Place", {"name": "New Delhi"})
    world.add_edge("u1", "pl1", "lives in")
    
    brain.world = world
    return brain


@pytest.fixture
def client(mock_brain):
    app.state.brain = mock_brain
    app.state.api_key = "test_graph_key"
    app.state.rate_limiter = SimpleRateLimiter(limit=100)
    with TestClient(app) as c:
        yield c


def test_api_graph_endpoints(client):
    """Verify REST API graph endpoints retrieve data, search, and explain."""
    # 1. GET /graph
    r = client.get("/graph", headers={"x-api-key": "test_graph_key"})
    assert r.status_code == 200
    assert "nodes" in r.json()
    assert "edges" in r.json()

    # 2. GET /graph/search
    r = client.get("/graph/search?query=new delhi", headers={"x-api-key": "test_graph_key"})
    assert r.status_code == 200
    assert len(r.json()["results"]) > 0

    # 3. GET /graph/explain
    r = client.get("/graph/explain?entity=faisal", headers={"x-api-key": "test_graph_key"})
    assert r.status_code == 200
    assert "lives in" in r.json()["explanation"]


def test_router_graph_routing(mock_brain):
    """Verify natural language queries are intercepted by the router."""
    router = Router(mock_brain)
    
    # Intercept check
    res = router.route("CHAT", text="What relates to Faisal?")
    assert "lives in 'New Delhi'" in res
