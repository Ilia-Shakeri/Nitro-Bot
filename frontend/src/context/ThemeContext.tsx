import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

type Theme = 'dark' | 'light';
interface ThemeCtx { theme: Theme; toggle: () => void; }

const Ctx = createContext<ThemeCtx>({ theme: 'dark', toggle: () => {} });

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem('nitro-theme') as Theme) ?? 'dark'
  );

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggle = () =>
    setTheme(t => {
      const next: Theme = t === 'dark' ? 'light' : 'dark';
      localStorage.setItem('nitro-theme', next);
      return next;
    });

  return <Ctx.Provider value={{ theme, toggle }}>{children}</Ctx.Provider>;
};

export const useTheme = () => useContext(Ctx);
