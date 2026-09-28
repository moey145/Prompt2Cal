// Outlook category hook: Graph has no per-event colour, so an event carries a
// category name and the mailbox decides its colour.
import { useEffect, useState } from "react";
import { makeApiCall } from "../utils/api";

export const useCategories = (userId, isAuthenticated, calendarProvider) => {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    let isMounted = true;

    const loadCategories = async () => {
      if (!userId || !isAuthenticated || calendarProvider !== "microsoft") {
        setCategories([]);
        return;
      }
      try {
        const response = await makeApiCall("/calendar_categories", {
          method: "GET",
          params: { user_id: userId, provider: calendarProvider },
        });
        if (isMounted && response.success) {
          setCategories(response.categories || []);
        }
      } catch (error) {
        // Categories are a nicety; failing to load them must not block editing.
        console.error("Failed to load categories:", error);
      }
    };

    loadCategories();
    return () => {
      isMounted = false;
    };
  }, [userId, isAuthenticated, calendarProvider]);

  return { categories };
};
