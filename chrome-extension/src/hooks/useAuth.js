// Authentication hook
import { useState, useEffect } from "react";
import { makeApiCall } from "../utils/api";

const hasChromeStorage = () =>
  typeof chrome !== "undefined" &&
  chrome.storage &&
  chrome.storage.local &&
  typeof chrome.storage.local.get === "function";

const cacheAuthStatus = async (isAuthed, provider = "google") => {
  if (!hasChromeStorage()) return;
  try {
    await chrome.storage.local.set({
      prompt2cal_auth_status: isAuthed,
      calendar_provider: provider,
    });
  } catch (error) {
    console.error("Failed to cache auth status:", error);
  }
};

const readCachedAuthStatus = async () => {
  if (!hasChromeStorage()) return { authenticated: null, provider: "google" };
  try {
    const result = await chrome.storage.local.get([
      "prompt2cal_auth_status",
      "calendar_provider",
    ]);
    return {
      authenticated:
        typeof result.prompt2cal_auth_status === "boolean"
          ? result.prompt2cal_auth_status
          : null,
      provider: result.calendar_provider || "google",
    };
  } catch (error) {
    console.error("Failed to read cached auth status:", error);
    return { authenticated: null, provider: "google" };
  }
};

export const useAuth = (userId) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [calendarProvider, setCalendarProvider] = useState("google");
  const [providers, setProviders] = useState({
    google: false,
    microsoft: false,
  });
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [loadingAuth, setLoadingAuth] = useState(false);
  const [loadingMicrosoftAuth, setLoadingMicrosoftAuth] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const initializeAuthState = async () => {
      const cached = await readCachedAuthStatus();
      if (!isMounted) return;

      if (cached.provider) {
        setCalendarProvider(cached.provider);
      }
      if (cached.authenticated === true) {
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

  const checkAuthStatus = async (userIdValue, preferredProvider) => {
    try {
      const stored = await chrome.storage.local.get(["calendar_provider"]);
      const provider =
        preferredProvider || stored.calendar_provider || calendarProvider || "google";

      const response = await makeApiCall("/auth/status", {
        method: "GET",
        params: {
          user_id: userIdValue || userId,
          provider,
        },
      });

      const nextProviders = response.providers || {
        google: provider === "google" ? response.authenticated : false,
        microsoft: provider === "microsoft" ? response.authenticated : false,
      };
      const activeProvider = response.provider || provider;
      const authenticated = Boolean(response.authenticated);

      setProviders(nextProviders);
      setCalendarProvider(activeProvider);
      setIsAuthenticated(authenticated);
      await cacheAuthStatus(authenticated, activeProvider);
      return authenticated;
    } catch (error) {
      console.error("Auth check failed:", error);
      setIsAuthenticated(false);
      await cacheAuthStatus(false, calendarProvider);
      return false;
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const startOAuth = async (endpoint, provider, setLoading) => {
    if (loadingAuth || loadingMicrosoftAuth) return;

    try {
      setLoading(true);

      const response = await makeApiCall(endpoint, {
        method: "GET",
        params: { user_id: userId },
      });

      await chrome.storage.local.set({
        waitingForAuth: true,
        calendar_provider: provider,
      });
      setCalendarProvider(provider);
      await chrome.tabs.create({ url: response.auth_url });
      window.close();
    } catch (error) {
      console.error("Auth error:", error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    await startOAuth("/auth/google", "google", setLoadingAuth);
  };

  const handleMicrosoftAuth = async () => {
    await startOAuth("/auth/microsoft", "microsoft", setLoadingMicrosoftAuth);
  };

  const switchProvider = async (provider, userIdValue) => {
    const next = provider === "microsoft" ? "microsoft" : "google";
    setCalendarProvider(next);
    await chrome.storage.local.set({ calendar_provider: next });
    // Clear calendar selection when switching providers
    await chrome.storage.local.remove(["selectedCalendarId"]);
    return checkAuthStatus(userIdValue || userId, next);
  };

  const handleLogout = async () => {
    try {
      const response = await makeApiCall("/auth/logout", {
        method: "POST",
        params: {
          user_id: userId,
          provider: calendarProvider,
        },
      });

      if (response.success) {
        const nextProviders = {
          ...providers,
          [calendarProvider]: false,
        };
        setProviders(nextProviders);

        // If the other provider is still connected, switch to it
        const fallback =
          calendarProvider === "google"
            ? nextProviders.microsoft
              ? "microsoft"
              : null
            : nextProviders.google
            ? "google"
            : null;

        if (fallback) {
          setCalendarProvider(fallback);
          setIsAuthenticated(true);
          await cacheAuthStatus(true, fallback);
          await chrome.storage.local.remove(["selectedCalendarId"]);
        } else {
          setIsAuthenticated(false);
          await cacheAuthStatus(false, calendarProvider);
        }
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
    loadingMicrosoftAuth,
    calendarProvider,
    providers,
    checkAuthStatus,
    handleGoogleAuth,
    handleMicrosoftAuth,
    handleLogout,
    switchProvider,
    setIsAuthenticated,
    setCalendarProvider,
  };
};
