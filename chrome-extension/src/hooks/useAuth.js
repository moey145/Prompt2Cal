// Authentication hook
import { useState, useEffect } from "react";
import { makeApiCall } from "../utils/api";

export const useAuth = (userId) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [loadingAuth, setLoadingAuth] = useState(false);

  const checkAuthStatus = async (userIdValue) => {
    try {
      const response = await makeApiCall("/auth/status", {
        method: "GET",
        params: { user_id: userIdValue || userId },
      });

      setIsAuthenticated(response.authenticated);
      return response.authenticated;
    } catch (error) {
      console.error("Auth check failed:", error);
      setIsAuthenticated(false);
      return false;
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const handleGoogleAuth = async () => {
    if (loadingAuth) return;

    try {
      setLoadingAuth(true);

      const response = await makeApiCall("/auth/google", {
        method: "GET",
        params: { user_id: userId },
      });

      await chrome.storage.local.set({ waitingForAuth: true });
      await chrome.tabs.create({ url: response.auth_url });
      window.close();
    } catch (error) {
      console.error("Auth error:", error);
      throw error;
    } finally {
      setLoadingAuth(false);
    }
  };

  const handleLogout = async () => {
    try {
      const response = await makeApiCall("/auth/logout", {
        method: "POST",
        params: { user_id: userId },
      });

      if (response.success) {
        setIsAuthenticated(false);
        return true;
      }
      return false;
    } catch (error) {
      console.error("Logout error:", error);
      throw error;
    }
  };

  return {
    isAuthenticated,
    isCheckingAuth,
    loadingAuth,
    checkAuthStatus,
    handleGoogleAuth,
    handleLogout,
    setIsAuthenticated,
  };
};

