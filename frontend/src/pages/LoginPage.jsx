import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, register } from '../services/auth';
import { usePreferences } from '../contexts/PreferencesContext';
import './LoginRegister.css';
import zxcvbn from 'zxcvbn';

function validateCNPJ(cnpj) {
  cnpj = cnpj.replace(/\D/g, '');
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

const LoginPage = () => {
  const { darkMode } = usePreferences();
  const [isRegister, setIsRegister] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({
    cnpj: '', fullName: '', birthDate: '', phone: '', email: '', password: '', passwordConfirm: ''
  });
  const [error, setError] = useState('');
  const [cnpjValid, setCnpjValid] = useState(true);
  const [emailValid, setEmailValid] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(null);
  const [passwordError, setPasswordError] = useState("");
  const [phoneValid, setPhoneValid] = useState(true);
  const [birthDateValid, setBirthDateValid] = useState(true);
  const [touched, setTouched] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    document.body.className = darkMode ? 'dark-mode' : '';
  }, [darkMode]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const params = new URLSearchParams();
      params.append('username', loginForm.email);
      params.append('password', loginForm.password);
      const { data } = await login(params);
      localStorage.setItem('access_token', data.access_token);
      navigate('/');
      window.location.reload();
    } catch (err) {
      setError('Usuário ou senha inválidos');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setTouched({
      fullName: true,
      birthDate: true,
      email: true,
      cnpj: true,
      phone: true,
      password: true,
      passwordConfirm: true
    });
    setError('');
    if (!validateCNPJ(registerForm.cnpj)) {
      setError('CNPJ inválido.');
      return;
    }
    if (!validateEmail(registerForm.email)) {
      setEmailValid(false);
      setError('Por favor, insira um email válido.');
      return;
    }
    if (registerForm.password !== registerForm.passwordConfirm) {
      setError('As senhas não coincidem.');
      return;
    }
    try {
      await register({
        cnpj: registerForm.cnpj.replace(/\D/g, ''),
        full_name: registerForm.fullName,
        birth_date: registerForm.birthDate,
        phone: registerForm.phone.replace(/\D/g, ''),
        email: registerForm.email,
        password: registerForm.password,
      });
      setIsRegister(false);
      setError('Cadastro realizado com sucesso! Faça login.');
    } catch (err) {
      setError('Erro ao registrar. Verifique os dados. ' + (err?.response?.data?.detail || ''));
    }
  };

  const handleCnpjChange = e => {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 14) value = value.slice(0, 14);
    let formatted = value;
    if (value.length > 2) formatted = value.slice(0,2) + '.' + value.slice(2);
    if (value.length > 5) formatted = formatted.slice(0,6) + '.' + formatted.slice(6);
    if (value.length > 8) formatted = formatted.slice(0,10) + '/' + formatted.slice(10);
    if (value.length > 12) formatted = formatted.slice(0,15) + '-' + formatted.slice(15);
    setRegisterForm(f => ({ ...f, cnpj: formatted }));
    setCnpjValid(validateCNPJ(value));
    setTouched(t => ({ ...t, cnpj: false }));
  };

  const validateEmail = (email) => {
    // Regex simples para validação de email
    return /^[\w-.]+@([\w-]+\.)+[\w-]{2,}$/.test(email);
  };

  const validatePhone = (phone) => {
    // Aceita (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
    return /^(\(\d{2}\)\s)?\d{4,5}-\d{4}$/.test(phone);
  };

  const validateBirthDate = (date) => {
    if (!date) return false;
    const today = new Date();
    const birth = new Date(date);
    const age = today.getFullYear() - birth.getFullYear();
    if (age < 18) return false;
    if (birth > today) return false;
    return true;
  };

  const handleRegisterChange = e => {
    const { name, value } = e.target;
    if (name === 'cnpj') {
      const numeric = value.replace(/\D/g, '');
      setRegisterForm(f => ({ ...f, [name]: numeric }));
      setCnpjValid(validateCNPJ(numeric));
    } else if (name === 'email') {
      setRegisterForm(f => ({ ...f, [name]: value }));
      setEmailValid(validateEmail(value));
    } else if (name === 'password' || name === 'passwordConfirm') {
      setRegisterForm(f => ({ ...f, [name]: value }));
      const result = zxcvbn(name === 'password' ? value : registerForm.password);
      setPasswordStrength(result.score);
      setPasswordError(result.score < 3 ? 'A senha deve ser forte (use letras, números e símbolos)' : '');
    } else if (name === 'phone') {
      setRegisterForm(f => ({ ...f, [name]: value }));
      setPhoneValid(validatePhone(value));
    } else if (name === 'birthDate') {
      setRegisterForm(f => ({ ...f, [name]: value }));
      setBirthDateValid(validateBirthDate(value));
    } else {
      setRegisterForm(f => ({ ...f, [name]: value }));
    }
    setTouched(t => ({ ...t, [name]: false }));
  };

  const handleBlur = e => {
    const { name } = e.target;
    setTouched(t => ({ ...t, [name]: true }));
  };

  const handlePhoneChange = e => {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 11) value = value.slice(0, 11);
    let formatted = value;
    if (value.length > 0) formatted = '(' + value.slice(0, 2);
    if (value.length >= 3) formatted += ') ' + value.slice(2, value.length > 10 ? 7 : 6);
    if (value.length > 6) formatted += '-' + value.slice(value.length > 10 ? 7 : 6, 11);
    setRegisterForm(f => ({ ...f, phone: formatted }));
    setTouched(t => ({ ...t, phone: false }));
  };

  return (
    <div className="login-register-container">
      {!isRegister ? (
        <form className="login-form" onSubmit={handleLogin}>
          <h2>Login</h2>
          <input type="text" placeholder="Email" value={loginForm.email} onChange={e => setLoginForm(f => ({ ...f, email: e.target.value }))} required />
          <input type="password" placeholder="Senha" value={loginForm.password} onChange={e => setLoginForm(f => ({ ...f, password: e.target.value }))} required />
          <button className="darkmode-toggle" type="submit">Entrar</button>
          <div className="register-link">
            Não possui um cadastro?{' '}
            <button type="button" className="link-btn" onClick={() => setIsRegister(true)}>Clique aqui</button>
          </div>
        </form>
      ) : (
        <form className="register-form" onSubmit={handleRegister}>
          <h2>Cadastro</h2>
          <div className="form-row">
            <input
              type="text"
              name="fullName"
              value={registerForm.fullName}
              onChange={handleRegisterChange}
              onBlur={handleBlur}
              placeholder="Nome completo*"
              required
              className={touched.fullName && !registerForm.fullName ? 'input-error' : ''}
              onInvalid={e => e.target.setCustomValidity('Preencha o nome completo')}
              onInput={e => e.target.setCustomValidity('')}
            />
            {touched.fullName && !registerForm.fullName && <span className="input-error-pop">Preencha o nome completo</span>}
          </div>
          <div className="form-row">
            <input
              type="date"
              name="birthDate"
              value={registerForm.birthDate}
              onChange={handleRegisterChange}
              onBlur={handleBlur}
              placeholder="Data de nascimento*"
              required
              className={touched.birthDate && !birthDateValid ? 'input-error' : ''}
              onFocus={e => e.target.showPicker && e.target.showPicker()}
              onInvalid={e => e.target.setCustomValidity('Informe uma data de nascimento válida')}
              onInput={e => e.target.setCustomValidity('')}
            />
            {touched.birthDate && !birthDateValid && <span className="input-error-pop">Você deve ser maior de 18 anos</span>}
          </div>
          <div className="form-row">
            <input
              type="email"
              name="email"
              value={registerForm.email}
              onChange={handleRegisterChange}
              onBlur={handleBlur}
              placeholder="Email*"
              required
              className={touched.email && !emailValid ? 'input-error' : ''}
              autoComplete="email"
              aria-invalid={!emailValid}
              aria-describedby={!emailValid ? 'email-error-pop' : undefined}
              onInvalid={e => e.target.setCustomValidity('Por favor, insira um email válido (ex: usuario@email.com)')}
              onInput={e => e.target.setCustomValidity('')}
            />
            {touched.email && !emailValid && (
              <span className="input-error-pop" id="email-error-pop">
                Por favor, insira um email válido (ex: usuario@email.com)
              </span>
            )}
          </div>
          <div className="form-row">
            <input
              type="text"
              name="cnpj"
              value={registerForm.cnpj}
              onChange={handleCnpjChange}
              onBlur={handleBlur}
              maxLength={18}
              placeholder="CNPJ*"
              required
              className={touched.cnpj && !cnpjValid ? 'input-error' : ''}
              onInvalid={e => e.target.setCustomValidity('CNPJ inválido')}
              onInput={e => e.target.setCustomValidity('')}
            />
            {touched.cnpj && !cnpjValid && <span className="input-error-pop">CNPJ inválido</span>}
          </div>
          <div className="form-row">
            <input
              type="tel"
              name="phone"
              value={registerForm.phone}
              onChange={handlePhoneChange}
              onBlur={handleBlur}
              placeholder="(XX) XXXXX-XXXX"
              required
              maxLength={15}
              className={touched.phone && !phoneValid ? 'input-error' : ''}
              onInvalid={e => e.target.setCustomValidity('Telefone inválido')}
              onInput={e => e.target.setCustomValidity('')}
            />
            {touched.phone && !phoneValid && <span className="input-error-pop">Telefone inválido</span>}
          </div>
          <div className="form-row-inline">
            <div className="input-with-icon">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={registerForm.password}
                onChange={handleRegisterChange}
                onBlur={handleBlur}
                placeholder="Senha*"
                required
                className={touched.password && passwordError ? 'input-error' : ''}
                onInvalid={e => e.target.setCustomValidity('Digite uma senha forte')}
                onInput={e => e.target.setCustomValidity('')}
              />
              <button
                type="button"
                className="eye-btn"
                tabIndex={-1}
                onMouseDown={() => setShowPassword(true)}
                onMouseUp={() => setShowPassword(false)}
                onMouseLeave={() => setShowPassword(false)}
                aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                style={{fontSize: '1rem', right: 2, width: 26, height: 26}}
              >
                {!showPassword ? '🙈' : '🐵'}
              </button>
              {touched.password && passwordError && <span className="input-error-pop">{passwordError}</span>}
            </div>
            <div className="input-with-icon">
              <input
                type={showPassword ? 'text' : 'password'}
                name="passwordConfirm"
                value={registerForm.passwordConfirm}
                onChange={handleRegisterChange}
                onBlur={handleBlur}
                placeholder="Confirme a Senha*"
                required
                className={touched.passwordConfirm && registerForm.password !== registerForm.passwordConfirm && registerForm.passwordConfirm ? 'input-error' : ''}
                onInvalid={e => e.target.setCustomValidity('Confirme a senha corretamente')}
                onInput={e => e.target.setCustomValidity('')}
              />
              <button
                type="button"
                className="eye-btn"
                tabIndex={-1}
                onMouseDown={() => setShowPassword(true)}
                onMouseUp={() => setShowPassword(false)}
                onMouseLeave={() => setShowPassword(false)}
                aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                style={{fontSize: '1rem', right: 2, width: 26, height: 26}}
              >
                {!showPassword ? '🙈' : '🐵'}
              </button>
              {touched.passwordConfirm && registerForm.password !== registerForm.passwordConfirm && registerForm.passwordConfirm && (
                <span className="input-error-pop">As senhas não coincidem</span>
              )}
            </div>
          </div>
          <button className="darkmode-toggle" type="submit">Cadastrar</button>
          <div className="register-link">
            Já tem conta?{' '}
            <button type="button" className="link-btn" onClick={() => setIsRegister(false)}>Entrar</button>
          </div>
        </form>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
};

export default LoginPage;
