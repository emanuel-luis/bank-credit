import React, { useEffect, useState } from 'react';
import { getCreditRequests, createCreditRequest, getRequestHistory, updateCreditRequestStatus, routeRequestToNext } from '../services/creditRequests';
import { usePreferences } from '../contexts/PreferencesContext';

const CreditRequestsPage = () => {
  const { darkMode } = usePreferences();
  const [requests, setRequests] = useState([]);
  const [amount, setAmount] = useState('');
  const [deliverDate, setDeliverDate] = useState('');
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  const fetchRequests = async () => {
    const { data } = await getCreditRequests();
    setRequests(data);
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  useEffect(() => {
    document.body.className = darkMode ? 'dark-mode' : '';
  }, [darkMode]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await createCreditRequest({ amount: parseFloat(amount), deliver_date: deliverDate });
      setAmount('');
      setDeliverDate('');
      fetchRequests();
    } catch (err) {
      setError('Erro ao criar solicitação.');
    }
  };

  const handleShowHistory = async (id) => {
    setSelectedId(id);
    const { data } = await getRequestHistory(id);
    setHistory(data);
  };

  const handleStatusUpdate = async (id, status) => {
    await updateCreditRequestStatus(id, status);
    fetchRequests();
  };

  const handleRouteNext = async (id) => {
    await routeRequestToNext(id);
    fetchRequests();
  };

  return (
    <div>
      <h2>Solicitações de Crédito</h2>
      <form onSubmit={handleCreate}>
        <input type="number" placeholder="Valor" value={amount} onChange={e => setAmount(e.target.value)} required />
        <input type="date" value={deliverDate} onChange={e => setDeliverDate(e.target.value)} required />
        <button className="darkmode-toggle" type="submit">Nova Solicitação</button>
      </form>
      {error && <div className="error">{error}</div>}
      <ul>
        {requests.map(req => (
          <li key={req.id}>
            <b>ID:</b> {req.id} | <b>Valor:</b> {req.amount} | <b>Status:</b> {req.status}
            <button className="darkmode-toggle" onClick={() => handleShowHistory(req.id)}>Histórico</button>
            <button className="darkmode-toggle" onClick={() => handleRouteNext(req.id)}>Encaminhar</button>
            <button className="darkmode-toggle" onClick={() => handleStatusUpdate(req.id, 'FINALIZED')}>Finalizar</button>
          </li>
        ))}
      </ul>
      {selectedId && (
        <div>
          <h3>Histórico da Solicitação {selectedId}</h3>
          <ul>
            {history.map((h, i) => (
              <li key={i}>{h.status} - {new Date(h.timestamp).toLocaleString()}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CreditRequestsPage;
