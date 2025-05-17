import pytest
from fastapi import status
from bank_credit.app.models import Process, Sector


@pytest.fixture
def process(db):
    sector = Sector(name="Test Sector", limit=100000.0, sla_days=2, require_all=True)
    db.add(sector)
    db.commit()
    db.refresh(sector)
    process = Process(name="Test Process", next_process_id=None)
    process.sectors.append(sector)
    db.add(process)
    db.commit()
    db.refresh(process)
    return process


def test_get_process_graph(authorized_client, db, process):
    response = authorized_client.get("/graph/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert any(node["id"] == process.id for node in data["nodes"])
    assert any("Test Sector" in node["sectors"] for node in data["nodes"])


def test_visualize_process_graph(authorized_client, db, process):
    response = authorized_client.get("/graph/visualize")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert any(node["id"] == process.id for node in data["nodes"])
    assert any(node["label"] == "Test Process" for node in data["nodes"])
