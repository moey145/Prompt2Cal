// Authentication hook
import { useState, useEffect } from "react";
import { makeApiCall } from "../utils/api";

const hasChromeStorage = () =>
  typeof chrome !== "undefined" &&
  chrome.storage &&
  chrome.storage.local &&
  typeof chrome.storage.local.get === "function";

const cacheAuthStatus = async (isAuthed) => {
  if (!hasChromeStorage()) return;
  try {
    await chrome.storage.local.set({
      prompt2cal_auth_status: isAuthed,
    });
  } catch (error) {
    console.error("Failed to cache auth status:", error);
  }
};

const readCachedAuthStatus = async () => {
  if (!hasChromeStorage()) return null;
  try {
    const result = await chrome.storage.local.get(["prompt2cal_auth_status"]);
    return typeof result.prompt2cal_auth_status === "boolean"
      ? result.prompt2cal_auth_status
      : null;
  } catch (error) {
    console.error("Failed to read cached auth status:", error);
    return null;
  }
};

export const useAuth = (userId) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [loadingAuth, setLoadingAuth] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const initializeAuthState = async () => {
      const cachedStatus = await readCachedAuthStatus();
      if (!isMounted) return;

      if (cachedStatus === true) {
        setIsAuthenticated(true);
        // keep isCheckingAuth true until server confirms status
      } else {
        setIsAuthenticated(false);
        setIsCheckingAuth(false);
      }
    };

    initializeAuthState();

    return () => {
      isMounted = false;
    };
  }, []);

  const checkAuthStatus = async (userIdValue) => {
    try {
      const response = await makeApiCall("/auth/status", {
        method: "GET",
        params: { user_id: userIdValue || userId },
      });

      setIsAuthenticated(response.authenticated);
      await cacheAuthStatus(response.authenticated);
      return response.authenticated;
    } catch (error) {
      console.error("Auth check failed:", error);
      setIsAuthenticated(false);
      await cacheAuthStatus(false);
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
        await cacheAuthStatus(false);
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

