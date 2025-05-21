# app/routers/graph.py

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import networkx as nx
import logging

from bank_credit.app.database import get_db
from bank_credit.app.routers.auth import get_current_active_user
from bank_credit.app import models
from bank_credit.app.views import utils as utils_view

logger = logging.getLogger("bank_credit.routers.graph")

router = APIRouter()


@router.get("/", response_class=JSONResponse, status_code=status.HTTP_200_OK)
def get_process_graph(
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    logger.info(f"[GET /graph] User {current_user.id}")
    try:
        G: nx.DiGraph = utils_view.get_process_graph_data(db)
        nodes = []
        for pid in G.nodes:
            proc: models.Process = db.query(models.Process).get(pid)
            if not proc:
                logger.warning(f"Process node {pid} not found in DB")
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
        edges = []
        for u, v in G.edges:
            edges.append({"from": u, "to": v})
        logger.debug(f"Graph nodes: {nodes}")
        logger.debug(f"Graph edges: {edges}")
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        logger.error(f"Error fetching process graph: {e}")
        raise


@router.get("/visualize", response_class=JSONResponse, status_code=status.HTTP_200_OK)
def visualize_process_graph(
    db: Session = Depends(get_db),
    current_user: models.Client = Depends(get_current_active_user),
):
    logger.info(f"[GET /graph/visualize] User {current_user.id}")
    try:
        G: nx.DiGraph = utils_view.get_process_graph_data(db)
        vis_nodes = []
        vis_edges = []
        for pid in G.nodes:
            proc: models.Process = db.query(models.Process).get(pid)
            if not proc:
                logger.warning(f"Process node {pid} not found in DB")
                continue
            vis_nodes.append({"id": proc.id, "label": proc.name})
        for u, v in G.edges:
            vis_edges.append({"from": u, "to": v})
        logger.debug(f"Vis.js nodes: {vis_nodes}")
        logger.debug(f"Vis.js edges: {vis_edges}")
        return {"nodes": vis_nodes, "edges": vis_edges}
    except Exception as e:
        logger.error(f"Error visualizing process graph: {e}")
        raise
