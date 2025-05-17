# app/routers/graph.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import networkx as nx

from bank_credit.app.database import get_db
from bank_credit.app.auth import get_current_active_user
from bank_credit.app import crud, models

router = APIRouter()


@router.get("/", response_class=JSONResponse, status_code=status.HTTP_200_OK)
def get_process_graph(
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Retorna a configuração completa do grafo de processos:
    - nodes: lista de processos (id, nome, processo seguinte, setores envolvidos)
    - edges: lista de arestas (de -> para)
    """
    # Apenas usuários autenticados podem ver a configuração do grafo
    G: nx.DiGraph = crud.get_process_graph_data(db)

    # Monta lista de nós com atributos
    nodes = []
    for pid in G.nodes:
        proc: models.Process = db.query(models.Process).get(pid)
        if not proc:
            continue
        sectors = [s.name for s in proc.sectors]
        nodes.append(
            {
                "id": proc.id,
                "name": proc.name,
                "next_process_id": proc.next_process_id,
                "sectors": sectors,
            }
        )

    # Monta lista de arestas
    edges = []
    for u, v in G.edges:
        edges.append({"from": u, "to": v})

    return {"nodes": nodes, "edges": edges}


@router.get("/visualize", response_class=JSONResponse, status_code=status.HTTP_200_OK)
def visualize_process_graph(
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    """
    Retorna uma representação simplificada do grafo em formato compatível
    com bibliotecas de visualização (por exemplo, vis.js).
    """
    G: nx.DiGraph = crud.get_process_graph_data(db)

    vis_nodes = []
    vis_edges = []

    # Vis.js espera campos: id, label
    for pid in G.nodes:
        proc: models.Process = db.query(models.Process).get(pid)
        if not proc:
            continue
        vis_nodes.append({"id": proc.id, "label": proc.name})

    for u, v in G.edges:
        vis_edges.append({"from": u, "to": v})

    return {"nodes": vis_nodes, "edges": vis_edges}
