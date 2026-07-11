import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { getUser } from '../api';
import type { User } from '../types/api';

interface UserContextValue {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<void>;
}

const UserContext = createContext<UserContextValue | null>(null);

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser]     = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { i18n } = useTranslation();

  const refreshUser = useCallback(async () => {
    try {
      const u = await getUser();
      setUser(u);
      i18n.changeLanguage(u.language_preference);
    } catch {
      // stay null; component-level error handling handles UI
    } finally {
      setLoading(false);
    }
  }, [i18n]);

  useEffect(() => {
    let active = true;
    const loadUser = async () => {
      try {
        const u = await getUser();
        if (!active) return;
        setUser(u);
        i18n.changeLanguage(u.language_preference);
      } catch {
        // stay null; component-level error handling handles UI
      } finally {
        if (active) setLoading(false);
      }
    };
    loadUser();
    return () => { active = false; };
  }, [i18n]);

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
