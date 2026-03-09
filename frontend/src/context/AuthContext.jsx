import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { clearStoredTokens, setStoredTokens } from "../services/api";
import { loginUser, meUser, logoutUser, registerUser } from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("clipai_token") || "");
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem("clipai_refresh_token") || "");
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("clipai_user");
    return raw ? JSON.parse(raw) : null;
  });

  useEffect(() => {
    if (!token) {
      return;
    }

    if (user) {
      return;
    }

    meUser(token)
      .then((profile) => {
        localStorage.setItem("clipai_user", JSON.stringify(profile));
        setUser(profile);
      })
      .catch(() => {
        clearStoredTokens();
        localStorage.removeItem("clipai_user");
        setToken("");
        setRefreshToken("");
        setUser(null);
      });
  }, [token, user]);

  const refreshUser = async () => {
    if (!token) {
      return null;
    }
    const profile = await meUser(token);
    localStorage.setItem("clipai_user", JSON.stringify(profile));
    setUser(profile);
    return profile;
  };

  const login = async ({ email, password }) => {
    const data = await loginUser({ email, password });
    setStoredTokens(data);
    setToken(data.access_token);
    setRefreshToken(data.refresh_token);

    const profile = await meUser(data.access_token);
    localStorage.setItem("clipai_user", JSON.stringify(profile));
    setUser(profile);
    return profile;
  };

  const register = async ({ email, password, full_name }) => {
    const data = await registerUser({ email, password, full_name });
    setStoredTokens(data);
    setToken(data.access_token);
    setRefreshToken(data.refresh_token);

    const profile = await meUser(data.access_token);
    localStorage.setItem("clipai_user", JSON.stringify(profile));
    setUser(profile);
    return profile;
  };

  const logout = async () => {
    try {
      if (token) {
        await logoutUser(token);
      }
    } catch {
      // ignore logout API errors and clear local state anyway
    } finally {
      clearStoredTokens();
        localStorage.removeItem("clipai_user");
        setToken("");
        setRefreshToken("");
        setUser(null);
    }
  };

  const value = useMemo(
    () => ({
      token,
      refreshToken,
      user,
      isAuthenticated: Boolean(token),
      login,
      register,
      logout,
      refreshUser,
      setUser,
    }),
    [token, refreshToken, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext doit etre utilise dans AuthProvider");
  }
  return context;
}
