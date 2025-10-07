"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import axios from 'axios';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { accessToken, refreshToken, setTokens, logout } = useAuthStore();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Wait for Zustand store to initialize from localStorage
    const timer = setTimeout(() => {
      setIsInitialized(true);
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isInitialized) return;

    const checkAuth = async () => {
      if (accessToken) {
        setIsLoading(false);
        return;
      }

      if (refreshToken) {
        try {
          // Try to refresh the token
          const response = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL}/api/auth/jwt/refresh/`,
            { refresh: refreshToken }
          );
          
          const { access } = response.data;
          setTokens(access, refreshToken);
          setIsLoading(false);
        } catch {
          // Refresh failed, logout user
          logout();
          router.push('/login');
        }
      } else {
        // No tokens, redirect to login
        router.push('/login');
      }
    };

    checkAuth();
  }, [isInitialized, accessToken, refreshToken, setTokens, logout, router]);

  if (!isInitialized || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  if (!accessToken) {
    return null; // Will redirect to login
  }

  return <>{children}</>;
}
