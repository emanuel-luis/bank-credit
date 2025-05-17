import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { register } from '../services/auth';
import { usePreferences } from '../contexts/PreferencesContext';

function validateCNPJ(cnpj) {
  cnpj = cnpj.replace(/[\D]/g, '');
  if (cnpj.length !== 14) return false;
  if (/^([0-9])\1+$/.test(cnpj)) return false;
  let t = cnpj.length - 2, d = cnpj.substring(t), d1 = parseInt(d.charAt(0)), d2 = parseInt(d.charAt(1)), calc = x => {
    let n = cnpj.substring(0, x), y = x - 7, s = 0, r = 0;
    for (let i = x; i >= 1; i--) {
      s += n.charAt(x - i) * y--;
      if (y < 2) y = 9;
    }
    r = 11 - s % 11;
    return r > 9 ? 0 : r;
  };
  return calc(t) === d1 && calc(t + 1) === d2;
}

const RegisterPage = () => {
  const { darkMode } = usePreferences();
  const [form, setForm] = useState({
    cnpj: '',
    fullName: '',
    birthDate: '',
    phone: '',
    email: '',
    emailConfirm: '',
    password: '',
    passwordConfirm: '',
  });
  const [error, setError] = useState('');
  const [cnpjValid, setCnpjValid] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    document.body.className = darkMode ? 'dark-mode' : '';
  }, [darkMode]);

  const formatCNPJ = (value) => {
    const cnpj = value.replace(/\D/g, '');
    return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5').replace(/[-/]\.$/, '');
  };

  const handleChange = e => {
    const { name, value } = e.target;
    if (name === 'cnpj') {
      const numeric = value.replace(/\D/g, '');
      setForm(f => ({ ...f, [name]: numeric }));
      setCnpjValid(validateCNPJ(numeric));
    } else {
      setForm(f => ({ ...f, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!validateCNPJ(form.cnpj)) {
      setError('CNPJ inválido.');
      return;
    }
    if (form.email !== form.emailConfirm) {
      setError('Os emails não coincidem.');
      return;
    }
    if (form.password !== form.passwordConfirm) {
      setError('As senhas não coincidem.');
      return;
    }
    try {
      await register({
        cnpj: form.cnpj,
        full_name: form.fullName,
        birth_date: form.birthDate,
        phone: form.phone,
        email: form.email,
        password: form.password,
      });
      navigate('/login');
    } catch (err) {
      setError('Erro ao registrar. Verifique os dados. ' + (err?.response?.data?.detail || ''));
    }
  };

  return (
    <div className="register-container">
      <h2>Cadastro</h2>
      <form onSubmit={handleSubmit} className="register-form">
        <div className="form-row">
          <label>CNPJ*</label>
          <input type="text" name="cnpj" value={formatCNPJ(form.cnpj)} onChange={handleChange} maxLength={18} placeholder="00.000.000/0000-00" required className={cnpjValid ? '' : 'invalid'} />
          {!cnpjValid && <span className="error">CNPJ inválido</span>}
        </div>
        <div className="form-row">
          <label>Nome completo*</label>
          <input type="text" name="fullName" value={form.fullName} onChange={handleChange} required />
        </div>
        <div className="form-row">
          <label>Data de nascimento*</label>
          <input type="date" name="birthDate" value={form.birthDate} onChange={handleChange} required />
        </div>
        <div className="form-row">
          <label>Telefone*</label>
          <input type="tel" name="phone" value={form.phone} onChange={handleChange} required placeholder="(99) 99999-9999" />
        </div>
        <div className="form-row">
          <label>Email*</label>
          <input type="email" name="email" value={form.email} onChange={handleChange} required />
        </div>
        <div className="form-row">
          <label>Confirme o Email*</label>
          <input type="email" name="emailConfirm" value={form.emailConfirm} onChange={handleChange} required />
        </div>
        <div className="form-row">
          <label>Senha*</label>
          <input type="password" name="password" value={form.password} onChange={handleChange} required />
        </div>
        <div className="form-row">
          <label>Confirme a Senha*</label>
          <input type="password" name="passwordConfirm" value={form.passwordConfirm} onChange={handleChange} required />
        </div>
        <button className="darkmode-toggle" type="submit">Cadastrar</button>
      </form>
      {error && <div className="error">{error}</div>}
      <p>Já tem conta? <a href="/login">Entrar</a></p>
    </div>
  );
};

export default RegisterPage;
