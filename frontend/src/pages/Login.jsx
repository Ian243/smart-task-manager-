import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';

const Login = () => {
  const [username, setUsername] = useState('manager@example.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface">
      <div className="max-w-md w-full glass-card p-8 m-4">
        <div className="flex flex-col items-center mb-8">
          <CheckCircle className="h-12 w-12 text-primary-500 mb-4" />
          <h2 className="text-3xl font-bold text-gray-900">Smart Tasks</h2>
          <p className="text-gray-500 mt-2">Sign in to your account</p>
        </div>
        
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-6 text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              className="input-field"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="w-full btn-primary py-3">
            Sign In
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-600 font-medium hover:text-primary-700">
              Register here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
