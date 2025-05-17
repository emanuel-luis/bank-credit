import React, { useEffect, useState } from 'react';
import { getProcessGraph, visualizeProcessGraph } from '../services/graph';
import { usePreferences } from '../contexts/PreferencesContext';

const GraphPage = () => {
  const { darkMode } = usePreferences();
  const [graph, setGraph] = useState(null);
  const [visGraph, setVisGraph] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    document.body.className = darkMode ? 'dark-mode' : '';
  }, [darkMode]);

  useEffect(() => {
    getProcessGraph().then(({ data }) => setGraph(data)).catch(() => setError('Erro ao buscar grafo.'));
    visualizeProcessGraph().then(({ data }) => setVisGraph(data)).catch(() => {});
  }, []);

  return (
    <div>
      <h2>Fluxo de Processos</h2>
      {error && <div className="error">{error}</div>}
      {graph && (
        <div>
          <h3>Configuração</h3>
          <ul>
            {graph.nodes.map((node) => (
              <li key={node.id}>
                <b>{node.name}</b> (ID: {node.id}) - Próximo: {node.next_process_id || 'Fim'}<br />
                Setores: {node.sectors.join(', ')}
              </li>
            ))}
          </ul>
          <h4>Arestas:</h4>
          <ul>
            {graph.edges.map((e, i) => (
              <li key={i}>{e.from} → {e.to}</li>
            ))}
          </ul>
        </div>
      )}
      {visGraph && (
        <div>
          <h3>Visualização Simplificada</h3>
          <ul>
            {visGraph.nodes.map((n) => (
              <li key={n.id}>{n.label}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default GraphPage;
