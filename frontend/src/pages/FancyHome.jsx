import React, { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { usePreferences } from '../contexts/PreferencesContext';
import './FancyHome.css';
import Carousel from '../components/Carousel';
import '../components/Carousel.css';

const successCases = [
  {
    img: '/success-case2.svg',
    name: 'Empresa XPTO',
    text: 'Conseguimos crédito em tempo recorde e com acompanhamento transparente em cada etapa. Recomendo!'
  },
  {
    img: '/vite.svg',
    name: 'Comércio ABC',
    text: 'A plataforma facilitou todo o processo, desde o cadastro até a aprovação. Atendimento excelente.'
  },
  {
    img: '/react.svg',
    name: 'Startup Inova',
    text: 'Acompanhar o status do pedido e receber notificações fez toda a diferença para nossa gestão.'
  },
  {
    img: '/success-case1.svg',
    name: 'Construtora Solidez',
    text: 'A análise de crédito foi rápida e o suporte sempre disponível. Plataforma nota 10!'
  },
  {
    img: '/success-case2.svg',
    name: 'AgroFácil',
    text: 'Conseguimos expandir nosso negócio graças à agilidade e transparência do sistema.'
  },
  {
    img: '/vite.svg',
    name: 'Tech Solutions',
    text: 'A integração com o banco foi perfeita e a experiência do usuário é incrível.'
  }
];

const advantages = [
  {
    title: 'Aprovação Rápida',
    desc: 'Processo digital, análise automatizada e resposta em até 24h para você não perder oportunidades.'
  },
  {
    title: 'Transparência Total',
    desc: 'Acompanhe cada etapa do seu pedido, receba notificações e saiba exatamente o status do seu crédito.'
  },
  {
    title: 'Suporte Especializado',
    desc: 'Equipe pronta para ajudar por chat, e-mail ou telefone. Atendimento humanizado e eficiente.'
  },
  {
    title: 'Segurança de Dados',
    desc: 'Tecnologia de ponta, criptografia e conformidade LGPD para proteger suas informações.'
  },
  {
    title: 'Plataforma Intuitiva',
    desc: 'Interface moderna, fácil de usar, acessível de qualquer dispositivo e sem burocracia.'
  }
];

const features = [
  'Login seguro com autenticação JWT',
  'Cadastro e acompanhamento de solicitações de crédito',
  'Notificações em tempo real',
  'Fluxo de processos visual e interativo',
  'Painel do cliente com histórico detalhado',
  'API moderna (FastAPI, React, Vite)',
  'Banco de dados robusto (PostgreSQL)',
  'Testes automatizados e alta cobertura',
  'Design responsivo e dark mode',
  'Integração com e-mail e notificações',
  'Arquitetura escalável e segura'
];

const FancyHome = () => {
  const { user } = useContext(AuthContext);
  const { darkMode, setDarkMode } = usePreferences();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate('/portal');
  }, [user, navigate]);

  return (
    <div className="fancy-home">
      <button
        className="floating-darkmode-toggle"
        onClick={() => setDarkMode(d => !d)}
        title="Alternar modo claro/escuro"
        style={{left: 24, bottom: 24, top: 'auto', position: 'fixed'}}
      >
        <span style={{fontSize: '1.2rem'}}>{darkMode ? '🌙' : '☀️'}</span>
      </button>
      <header className="landing-header full-width-header" style={{padding: '0 32px', minHeight: 90}}>
        <div className="header-center">
          <img src="/vite.svg" alt="Logo" className="site-logo" style={{height: 70, width: 70, marginRight: 18}} />
          <span className="company-name" style={{fontSize: '2.2rem', letterSpacing: 2}}>Bank Credit System</span>
        </div>
        <a className="login-btn" style={{fontSize: '1.15rem', padding: '14px 32px', borderRadius: 8, fontWeight: 700, boxShadow: '0 2px 12px #1976d233'}} href="/login">Entrar</a>
      </header>
      <section className="hero-section">
        <div className="hero-content">
          <h1>Solicite crédito bancário de forma moderna, segura e transparente</h1>
          <p className="hero-subtitle">A plataforma que simplifica o acesso ao crédito para empresas e pessoas, com acompanhamento em tempo real e suporte especializado.</p>
          <div className="fancy-actions" style={{display: 'flex', justifyContent: 'center', width: '100%'}}>
            <a className="fancy-btn" style={{fontSize: '1.35rem', padding: '1.1em 2.5em', borderRadius: 12, fontWeight: 700, boxShadow: '0 2px 12px #1976d233'}} href="/login?tab=register">Abra sua conta grátis</a>
          </div>
        </div>
        <img src="/success-case1.svg" alt="Sucesso" className="hero-image" />
      </section>
      <section className="success-cases-section">
        <h2>Casos de Sucesso</h2>
        <Carousel visibleCount={3} items={successCases.map((c, i) => (
          <div className="success-case" key={i}>
            <img src={c.img} alt={c.name} />
            <h4>{c.name}</h4>
            <p>"{c.text}"</p>
          </div>
        ))} />
      </section>
      <section className="advantages-section">
        <h2>Por que escolher o Bank Credit System?</h2>
        <div className="advantages">
          {advantages.map((adv, i) => (
            <div className="advantage" key={i}>
              <h4>{adv.title}</h4>
              <p>{adv.desc}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="features-section" style={{background: '#f4f8ff', padding: '2.5rem 0'}}>
        <h2 style={{color: '#1976d2'}}>Tecnologias e Features</h2>
        <ul style={{maxWidth: 900, margin: '0 auto', textAlign: 'left', fontSize: '1.13rem', color: '#222', lineHeight: 1.7, columns: 2, columnGap: 48}}>
          {features.map((f, i) => <li key={i}>{f}</li>)}
        </ul>
      </section>
    </div>
  );
};

export default FancyHome;
