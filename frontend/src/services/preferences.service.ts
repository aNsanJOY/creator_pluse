import api from "./api";

// Types for user preferences
export interface UserPreferences {
  // Schedule & Frequency
  draft_schedule_time: string;
  newsletter_frequency: "daily" | "weekly" | "custom";

  // Tone preferences
  tone_preferences: {
    formality: "casual" | "balanced" | "formal";
    enthusiasm: "low" | "moderate" | "high";
    length_preference: "short" | "medium" | "long";
    use_emojis: boolean;
  };

  // Notification preferences
  notification_preferences: {
    email_on_draft_ready: boolean;
    email_on_publish_success: boolean;
    email_on_errors: boolean;
    weekly_summary: boolean;
  };

  // Email preferences
  email_preferences: {
    default_subject_template: string;
    include_preview_text: boolean;
    track_opens: boolean;
    track_clicks: boolean;
  };
  use_voice_profile: boolean;
}

// Type for preference updates (partial updates)
export type PreferencesUpdate = Partial<{
  draft_schedule_time: string;
  newsletter_frequency: "daily" | "weekly" | "custom";
  tone_preferences: Partial<UserPreferences["tone_preferences"]>;
  notification_preferences: Partial<
    UserPreferences["notification_preferences"]
  >;
  email_preferences: Partial<UserPreferences["email_preferences"]>;
  use_voice_profile: boolean;
}>;

// Default preferences
const DEFAULT_PREFERENCES: UserPreferences = {
  draft_schedule_time: "09:00",
  newsletter_frequency: "weekly",
  tone_preferences: {
    formality: "balanced",
    enthusiasm: "moderate",
    length_preference: "medium",
    use_emojis: true,
  },

  notification_preferences: {
    email_on_draft_ready: true,
    email_on_publish_success: true,
    email_on_errors: true,
    weekly_summary: false,
  },

  email_preferences: {
    default_subject_template: "{title} - Weekly Newsletter",
    include_preview_text: true,
    track_opens: false,
    track_clicks: false,
  },
  use_voice_profile: false,
};

class PreferencesService {
  async getPreferences(): Promise<UserPreferences> {
    try {
      const response = await api.get("/api/user/preferences");
      return response.data;
    } catch (error: any) {
      console.error("Failed to fetch preferences:", error);
      // Return defaults if API fails
      return { ...DEFAULT_PREFERENCES };
    }
  }

  async updatePreferences(
    updates: PreferencesUpdate
  ): Promise<UserPreferences> {
    try {
      const response = await api.patch("/api/user/preferences", updates);
      return response.data;
    } catch (error: any) {
      console.error("Failed to update preferences:", error);
      throw error;
    }
  }

  async resetPreferences(): Promise<UserPreferences> {
    try {
      const response = await api.post("/api/user/preferences/reset");
      return response.data;
    } catch (error: any) {
      console.error("Failed to reset preferences:", error);
      throw error;
    }
  }
}

const preferencesService = new PreferencesService();
export default preferencesService;
