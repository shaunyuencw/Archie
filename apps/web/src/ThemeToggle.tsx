import {useCallback, useLayoutEffect, useState} from 'react';
import {Moon, Sun} from 'lucide-react';
import './theme.css';

export type Theme = 'light' | 'dark';
const storageKey = 'archie.theme';
const savedTheme = (): Theme => {
  try { return localStorage.getItem(storageKey) === 'dark' ? 'dark' : 'light'; }
  catch { return 'light'; }
};

/** A device preference, separate from saved architectures and their exports. */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(savedTheme);
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(storageKey, theme); } catch { /* Private browsers may disable storage. */ }
  }, [theme]);
  useLayoutEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key === storageKey || event.key === null) setTheme(savedTheme());
    };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);
  const toggleTheme = useCallback(() => setTheme(value => value === 'dark' ? 'light' : 'dark'), []);
  return {theme, toggleTheme};
}

export function ThemeToggle({theme, onToggle}: {theme: Theme; onToggle: () => void}) {
  return <button type="button" className="theme-toggle" aria-label="Dark mode" aria-pressed={theme === 'dark'} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} onClick={onToggle}>
    {theme === 'dark' ? <Moon size={15} aria-hidden="true"/> : <Sun size={15} aria-hidden="true"/>}
    <span>{theme === 'dark' ? 'Dark' : 'Light'}</span>
  </button>;
}
