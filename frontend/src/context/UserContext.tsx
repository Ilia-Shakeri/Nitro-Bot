import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { getUser } from '../api';
import type { User } from '../types/api';
import { useToast } from './ToastContext';
import { errorText } from '../utils/formMessages';

interface UserContextValue {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<void>;
}

const UserContext = createContext<UserContextValue | null>(null);
const USER_REFRESH_INTERVAL_MS = 15_000;

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser]     = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { i18n } = useTranslation();
  const { toast } = useToast();
  const mountedRef = useRef(true);

  const loadUser = useCallback(async (showError: boolean) => {
    try {
      const u = await getUser();
      if (!mountedRef.current) return;
      setUser(u);
      await i18n.changeLanguage(u.language_preference);
    } catch (error) {
      if (mountedRef.current && showError) toast(errorText(error, i18n.t), 'error');
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [i18n, toast]);

  const refreshUser = useCallback(() => loadUser(true), [loadUser]);

  useEffect(() => {
    mountedRef.current = true;
    const initialLoad = globalThis.setTimeout(() => void loadUser(true), 0);
    return () => {
      mountedRef.current = false;
      globalThis.clearTimeout(initialLoad);
    };
  }, [loadUser]);

  useEffect(() => {
    const refreshWhenVisible = () => {
      if (document.visibilityState === 'visible') void loadUser(false);
    };
    const timer = globalThis.setInterval(refreshWhenVisible, USER_REFRESH_INTERVAL_MS);
    window.addEventListener('focus', refreshWhenVisible);
    document.addEventListener('visibilitychange', refreshWhenVisible);
    return () => {
      globalThis.clearInterval(timer);
      window.removeEventListener('focus', refreshWhenVisible);
      document.removeEventListener('visibilitychange', refreshWhenVisible);
    };
  }, [loadUser]);

  return (
    <UserContext.Provider value={{ user, loading, refreshUser }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error('useUser must be used inside UserProvider');
  return ctx;
};
