import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, LoginResponse } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, code?: string) => Promise<LoginResponse>;
  verify2FA: (tempToken: string, code: string) => Promise<LoginResponse>;
  register: (email: string, password: string, fullName?: string) => Promise<LoginResponse>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = async () => {
    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch (err) {
      console.warn('Failed to fetch authenticated user profile:', err);
      // If token expired/invalid, clear local token
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const handleAuthSuccess = (res: LoginResponse) => {
    if (res.access_token) {
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      fetchCurrentUser();
    }
  };

  const login = async (email: string, password: string, code?: string): Promise<LoginResponse> => {
    const res = await api.login(email, password, code);
    if (!res.requires_2fa && res.access_token) {
      handleAuthSuccess(res);
    }
    return res;
  };

  const verify2FA = async (tempToken: string, code: string): Promise<LoginResponse> => {
    const res = await api.verify2FALogin(tempToken, code);
    if (res.access_token) {
      handleAuthSuccess(res);
    }
    return res;
  };

  const register = async (email: string, password: string, fullName?: string): Promise<LoginResponse> => {
    const res = await api.register(email, password, fullName);
    if (res.access_token) {
      handleAuthSuccess(res);
    }
    return res;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    await fetchCurrentUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        verify2FA,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
