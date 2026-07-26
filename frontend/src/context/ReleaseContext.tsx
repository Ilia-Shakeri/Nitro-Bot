import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { getRelease, getReleases } from '../api';
import type { Release } from '../types/api';

interface ReleaseContextValue {
  releases: Release[] | null;
  loading: boolean;
  loadReleases: (force?: boolean) => Promise<Release[]>;
  loadRelease: (id: number) => Promise<Release>;
  invalidateReleases: () => void;
}

const ReleaseContext = createContext<ReleaseContextValue | null>(null);

export const ReleaseProvider = ({ children }: { children: ReactNode }) => {
  const [releases, setReleases] = useState<Release[] | null>(null);
  const [loading, setLoading] = useState(false);
  const releasesRef = useRef<Release[] | null>(null);
  const inflight = useRef<Promise<Release[]> | null>(null);

  const loadReleases = useCallback(async (force = false) => {
    if (!force && releasesRef.current) return releasesRef.current;
    if (!force && inflight.current) return inflight.current;
    setLoading(true);
    const request = getReleases()
      .then(value => {
        releasesRef.current = value;
        setReleases(value);
        return value;
      })
      .finally(() => {
        inflight.current = null;
        setLoading(false);
      });
    inflight.current = request;
    return request;
  }, []);

  const loadRelease = useCallback(async (id: number) => {
    const cached = releasesRef.current?.find(release => release.id === id);
    if (cached) return cached;
    const release = await getRelease(id);
    if (releasesRef.current) {
      releasesRef.current = [
        release,
        ...releasesRef.current.filter(item => item.id !== release.id),
      ];
      setReleases(releasesRef.current);
    }
    return release;
  }, []);

  const invalidateReleases = useCallback(() => {
    releasesRef.current = null;
    setReleases(null);
  }, []);

  return (
    <ReleaseContext.Provider value={{
      releases,
      loading,
      loadReleases,
      loadRelease,
      invalidateReleases,
    }}>
      {children}
    </ReleaseContext.Provider>
  );
};

export const useReleases = () => {
  const value = useContext(ReleaseContext);
  if (!value) throw new Error('useReleases must be used inside ReleaseProvider');
  return value;
};
