import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import userService, { UpdateProfileData } from "../services/user.service";
import preferencesService, {
  UserPreferences,
  PreferencesUpdate,
} from "../services/preferences.service";
import { Navigation } from "../components/Navigation";
import { Button } from "../components/ui/Button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/Dialog";
import { useToast } from "../components/ui/Toast";
import {
  User,
  Trash2,
  AlertTriangle,
  Settings,
  Bell,
  Mail,
  FileText,
  Clock,
  RotateCcw,
  UserCircle,
} from "lucide-react";

export function Profile() {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState("");

  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Preferences state
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [localPreferences, setLocalPreferences] = useState<UserPreferences | null>(null);
  const [isLoadingPreferences, setIsLoadingPreferences] = useState(true);
  const [isUpdatingPreferences, setIsUpdatingPreferences] = useState(false);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || "");
      setEmail(user.email || "");
    }
  }, [user]);

  // Load preferences
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const prefs = await preferencesService.getPreferences();
        setPreferences(prefs);
        setLocalPreferences(prefs);
      } catch (error: any) {
        console.error("Failed to load preferences:", error);
      } finally {
        setIsLoadingPreferences(false);
      }
    };
    loadPreferences();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdateError("");
    setIsUpdating(true);

    try {
      const updateData: UpdateProfileData = {};

      if (fullName !== user?.full_name) {
        updateData.full_name = fullName;
      }

      if (email !== user?.email) {
        updateData.email = email;
      }

      if (Object.keys(updateData).length === 0) {
        setUpdateError("No changes to update");
        setIsUpdating(false);
        return;
      }

      await userService.updateProfile(updateData);
      await refreshUser();

      addToast({
        type: "success",
        title: "Profile Updated",
        message: "Your profile has been successfully updated.",
      });

      setTimeout(() => setUpdateError(""), 3000);
    } catch (error: any) {
      setUpdateError(
        error.response?.data?.detail || "Failed to update profile"
      );
      addToast({
        type: "error",
        title: "Update Failed",
        message: error.response?.data?.detail || "Failed to update profile",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);

    try {
      await userService.deleteAccount();
      await logout();
      navigate("/signup", {
        state: { message: "Your account has been successfully deleted" },
      });
    } catch (error: any) {
      setIsDeleting(false);
      addToast({
        type: "error",
        title: "Delete Failed",
        message: error.response?.data?.detail || "Failed to delete account",
      });
    }
  };

  // Update local preferences without saving
  const handleLocalPreferenceChange = (updates: PreferencesUpdate) => {
    if (!localPreferences) return;
    
    const updated = { ...localPreferences };
    
    if (updates.draft_schedule_time !== undefined) {
      updated.draft_schedule_time = updates.draft_schedule_time;
    }
    if (updates.newsletter_frequency !== undefined) {
      updated.newsletter_frequency = updates.newsletter_frequency;
    }
    if (updates.use_voice_profile !== undefined) {
      updated.use_voice_profile = updates.use_voice_profile;
    }
    if (updates.tone_preferences !== undefined) {
      updated.tone_preferences = { ...updated.tone_preferences, ...updates.tone_preferences };
    }
    if (updates.notification_preferences !== undefined) {
      updated.notification_preferences = { ...updated.notification_preferences, ...updates.notification_preferences };
    }
    if (updates.email_preferences !== undefined) {
      updated.email_preferences = { ...updated.email_preferences, ...updates.email_preferences };
    }
    
    setLocalPreferences(updated);
    setHasUnsavedChanges(true);
  };

  // Save all preferences changes
  const handleSavePreferences = async () => {
    if (!localPreferences) return;
    
    setIsUpdatingPreferences(true);

    try {
      const updatedPrefs = await preferencesService.updatePreferences(localPreferences);
      setPreferences(updatedPrefs);
      setLocalPreferences(updatedPrefs);
      setHasUnsavedChanges(false);

      addToast({
        type: "success",
        title: "Preferences Updated",
        message: "Your settings have been saved successfully.",
      });
    } catch (error: any) {
      addToast({
        type: "error",
        title: "Update Failed",
        message: error.response?.data?.detail || "Failed to update preferences",
      });
    } finally {
      setIsUpdatingPreferences(false);
    }
  };

  // Discard unsaved changes
  const handleDiscardChanges = () => {
    setLocalPreferences(preferences);
    setHasUnsavedChanges(false);
  };

  const handleResetPreferences = async () => {
    setIsUpdatingPreferences(true);

    try {
      const resetPrefs = await preferencesService.resetPreferences();
      setPreferences(resetPrefs);
      setLocalPreferences(resetPrefs);
      setHasUnsavedChanges(false);
      setShowResetDialog(false);

      addToast({
        type: "success",
        title: "Preferences Reset",
        message: "All preferences have been reset to their default values.",
      });
    } catch (error: any) {
      addToast({
        type: "error",
        title: "Reset Failed",
        message: error.response?.data?.detail || "Failed to reset preferences",
      });
    } finally {
      setIsUpdatingPreferences(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Navigation currentPage="Profile" />

      {/* Profile Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6">
            <div className="flex-shrink-0 mx-auto sm:mx-0">
              <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-xl sm:text-2xl font-bold">
                {user?.full_name ? (
                  user.full_name
                    .trim()
                    .split(" ")
                    .filter((n: string) => n.length > 0)
                    .map((n: string) => n[0])
                    .join("")
                    .toUpperCase()
                    .slice(0, 2)
                ) : (
                  <UserCircle className="w-8 h-8 sm:w-10 sm:h-10" />
                )}
              </div>
            </div>
            <div className="flex-1 min-w-0 text-center sm:text-left">
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 truncate">
                Welcome back, {user?.full_name || "User"}!
              </h1>
              <p className="text-base sm:text-lg text-gray-600 mt-1">
                Manage your account settings and preferences
              </p>
              <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4 mt-3 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  Account Active
                </span>
                {user?.created_at && (
                  <>
                    <span className="hidden sm:inline">•</span>
                    <span>
                      Member since {new Date(user.created_at).getFullYear()}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Profile & Account Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Profile Information Card */}
          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5 text-blue-600" />
                Profile Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div>
                  <label
                    htmlFor="fullName"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Full Name
                  </label>
                  <Input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Enter your full name"
                  />
                </div>

                <div>
                  <label
                    htmlFor="email"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Email Address
                  </label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    required
                  />
                </div>

                {updateError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                    {updateError}
                  </div>
                )}

                <div className="flex justify-end">
                  <Button type="submit" disabled={isUpdating}>
                    {isUpdating ? "Updating..." : "Update Profile"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Account Information Card */}
          <Card className="hover:shadow-md transition-shadow duration-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-600" />
                Account Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">
                  Account Status
                </span>
                <span className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  Active
                </span>
              </div>
              {user?.created_at && (
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">
                    Member Since
                  </span>
                  <span className="text-sm text-gray-600">
                    {new Date(user.created_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">
                  Account Type
                </span>
                <span className="text-sm text-gray-600">Free Plan</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Preferences Section */}
        {isLoadingPreferences ? (
          <Card>
            <CardHeader>
              <div className="animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-48 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-64"></div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200 animate-pulse"
                  >
                    <div className="w-6 h-6 bg-gray-200 rounded-full mx-auto mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-16 mx-auto mb-1"></div>
                    <div className="h-4 bg-gray-200 rounded w-12 mx-auto"></div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ) : (
          preferences && (
            <div className="space-y-6">
              {/* Preferences Overview */}
              <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="w-5 h-5 text-blue-600" />
                    Quick Settings Overview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow">
                      <Clock className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500 mb-1">Draft Time</p>
                      <p className="text-sm font-medium text-gray-900">
                        {localPreferences?.draft_schedule_time || preferences?.draft_schedule_time}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow">
                      <FileText className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500 mb-1">Tone</p>
                      <p className="text-sm font-medium text-gray-900 capitalize">
                        {localPreferences?.tone_preferences.formality || preferences?.tone_preferences.formality}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow">
                      <Bell className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500 mb-1">
                        Notifications
                      </p>
                      <p className="text-sm font-medium text-gray-900">
                        {
                          Object.values(
                            localPreferences?.notification_preferences || preferences?.notification_preferences || {}
                          ).filter(Boolean).length
                        }{" "}
                        enabled
                      </p>
                    </div>
                    <div className="text-center p-4 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow">
                      <Mail className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500 mb-1">Frequency</p>
                      <p className="text-sm font-medium text-gray-900 capitalize">
                        {localPreferences?.newsletter_frequency || preferences?.newsletter_frequency}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Preferences Grid */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Schedule & Frequency Preferences */}
                <Card className="hover:shadow-md transition-shadow duration-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="w-5 h-5 text-blue-600" />
                      Schedule & Frequency
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <label
                        htmlFor="scheduleTime"
                        className="block text-sm font-medium text-gray-700 mb-1"
                      >
                        Draft Generation Time
                      </label>
                      <Input
                        id="scheduleTime"
                        type="time"
                        value={localPreferences?.draft_schedule_time || ""}
                        onChange={(e) =>
                          handleLocalPreferenceChange({
                            draft_schedule_time: e.target.value,
                          })
                        }
                        disabled={isUpdatingPreferences}
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Time when daily drafts will be generated
                      </p>
                    </div>

                    <div>
                      <label
                        htmlFor="frequency"
                        className="block text-sm font-medium text-gray-700 mb-1"
                      >
                        Newsletter Frequency
                      </label>
                      <select
                        id="frequency"
                        value={localPreferences?.newsletter_frequency || "weekly"}
                        onChange={(e) =>
                          handleLocalPreferenceChange({
                            newsletter_frequency: e.target.value as
                              | "daily"
                              | "weekly"
                              | "custom",
                          })
                        }
                        disabled={isUpdatingPreferences}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="custom">Custom</option>
                      </select>
                    </div>
                  </CardContent>
                </Card>

                {/* Tone Preferences */}
                <Card className="hover:shadow-md transition-shadow duration-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-blue-600" />
                      Tone & Style Preferences
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Voice Profile Switch */}
                    <div className="pb-6 border-b border-gray-200">
                      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
                        <div className="flex-1">
                          <label
                            htmlFor="useVoiceProfile"
                            className="block text-sm font-medium text-gray-900 mb-1"
                          >
                            Use Voice Profile
                          </label>
                          <p className="text-xs text-gray-600">
                            {localPreferences?.use_voice_profile
                              ? "Generate drafts using your analyzed writing voice"
                              : "Voice profile not available. Using tone preferences."}
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer ml-4">
                          <input
                            id="useVoiceProfile"
                            type="checkbox"
                            checked={localPreferences?.use_voice_profile || false}
                            onChange={(e) =>
                              handleLocalPreferenceChange({
                                use_voice_profile: e.target.checked,
                              })
                            }
                            disabled={isUpdatingPreferences}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
                        </label>
                      </div>
                      {!localPreferences?.use_voice_profile && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-3">
                          <p className="text-sm text-yellow-800">
                            <strong>Tip:</strong> Upload newsletter samples in
                            the Voice Analysis section to enable voice profile
                            generation.
                          </p>
                        </div>
                      )}
                      {localPreferences?.use_voice_profile && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
                          <p className="text-sm text-blue-800">
                            ✓ Drafts will be generated using your unique writing
                            voice profile
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Tone Preferences - Disabled when voice profile is active */}
                    <div
                      className={
                        localPreferences?.use_voice_profile
                          ? "opacity-50 pointer-events-none"
                          : ""
                      }
                    >
                      <div>
                        <label
                          htmlFor="formality"
                          className="block text-sm font-medium text-gray-700 mb-1"
                        >
                          Formality Level
                        </label>
                        <select
                          id="formality"
                          value={localPreferences?.tone_preferences.formality || "balanced"}
                          onChange={(e) =>
                            handleLocalPreferenceChange({
                              tone_preferences: {
                                formality: e.target.value as
                                  | "casual"
                                  | "balanced"
                                  | "formal",
                              },
                            })
                          }
                          disabled={isUpdatingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="casual">
                            Casual - Friendly and conversational
                          </option>
                          <option value="balanced">
                            Balanced - Professional yet approachable
                          </option>
                          <option value="formal">
                            Formal - Business-like and structured
                          </option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">
                          Choose how formal your newsletter content should be
                        </p>
                      </div>

                      <div>
                        <label
                          htmlFor="enthusiasm"
                          className="block text-sm font-medium text-gray-700 mb-1"
                        >
                          Enthusiasm Level
                        </label>
                        <select
                          id="enthusiasm"
                          value={localPreferences?.tone_preferences.enthusiasm || "moderate"}
                          onChange={(e) =>
                            handleLocalPreferenceChange({
                              tone_preferences: {
                                enthusiasm: e.target.value as
                                  | "low"
                                  | "moderate"
                                  | "high",
                              },
                            })
                          }
                          disabled={isUpdatingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="low">
                            Low - Matter-of-fact and straightforward
                          </option>
                          <option value="moderate">
                            Moderate - Enthusiastic but not overwhelming
                          </option>
                          <option value="high">
                            High - Very excited and energetic
                          </option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">
                          Control the energy level of your newsletter content
                        </p>
                      </div>

                      <div>
                        <label
                          htmlFor="length"
                          className="block text-sm font-medium text-gray-700 mb-1"
                        >
                          Content Length
                        </label>
                        <select
                          id="length"
                          value={localPreferences?.tone_preferences.length_preference || "medium"}
                          onChange={(e) =>
                            handleLocalPreferenceChange({
                              tone_preferences: {
                                length_preference: e.target.value as
                                  | "short"
                                  | "medium"
                                  | "long",
                              },
                            })
                          }
                          disabled={isUpdatingPreferences}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="short">
                            Short - Concise and to the point
                          </option>
                          <option value="medium">
                            Medium - Balanced length with good detail
                          </option>
                          <option value="long">
                            Long - Comprehensive with full explanations
                          </option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">
                          Set the preferred length for your newsletter content
                        </p>
                      </div>

                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="useEmojis"
                            type="checkbox"
                            checked={localPreferences?.tone_preferences.use_emojis || false}
                            onChange={(e) =>
                              handleLocalPreferenceChange({
                                tone_preferences: {
                                  use_emojis: e.target.checked,
                                },
                              })
                            }
                            disabled={isUpdatingPreferences}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3">
                          <label
                            htmlFor="useEmojis"
                            className="text-sm font-medium text-gray-700"
                          >
                            Use emojis in content
                          </label>
                          <p className="text-xs text-gray-500 mt-1">
                            Add emojis to make your newsletter more engaging and
                            visual
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Full-width sections */}
              <div className="space-y-6">
                {/* Notification Preferences */}
                <Card className="hover:shadow-md transition-shadow duration-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Bell className="w-5 h-5 text-blue-600" />
                      Notifications
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="flex-1">
                          <label
                            htmlFor="emailDraftReady"
                            className="text-sm font-medium text-gray-700 block"
                          >
                            Email on draft ready
                          </label>
                          <p className="text-xs text-gray-500 mt-1">
                            Get notified when a new draft is generated and ready
                            for review
                          </p>
                        </div>
                        <input
                          id="emailOnDraftReady"
                          type="checkbox"
                          checked={
                            localPreferences?.notification_preferences
                              .email_on_draft_ready || false
                          }
                          onChange={(e) =>
                            handleLocalPreferenceChange({
                              notification_preferences: {
                                email_on_draft_ready: e.target.checked,
                              },
                            })
                          }
                          disabled={isUpdatingPreferences}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </div>

                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="flex-1">
                          <label
                            htmlFor="emailOnPublishSuccess"
                            className="text-sm font-medium text-gray-700 block"
                          >
                            Email on publish success
                          </label>
                          <p className="text-xs text-gray-500 mt-1">
                            Get notified when your newsletter is successfully
                            published
                          </p>
                        </div>
                        <input
                          id="emailOnPublishSuccess"
                          type="checkbox"
                          checked={
                            localPreferences?.notification_preferences
                              .email_on_publish_success || false
                          }
                          onChange={(e) =>
                            handleLocalPreferenceChange({
                              notification_preferences: {
                                email_on_publish_success: e.target.checked,
                              },
                            })
                          }
                          disabled={isUpdatingPreferences}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </div>

                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="flex-1">
                          <label
                            htmlFor="emailOnErrors"
                            className="text-sm font-medium text-gray-700 block"
                          >
                            Email on errors
                          </label>
                          <p className="text-xs text-gray-500 mt-1">
                            Get notified when errors occur during draft
                            generation or publishing
                          </p>
                        </div>
                        <input
                          id="emailOnErrors"
                          type="checkbox"
                          checked={
                            localPreferences?.notification_preferences.email_on_errors || false
                          }
                          onChange={(e) =>
                            handleLocalPreferenceChange({
                              notification_preferences: {
                                email_on_errors: e.target.checked,
                              },
                            })
                          }
                          disabled={isUpdatingPreferences}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </div>

                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="flex-1">
                          <label
                            htmlFor="weeklySummary"
                            className="text-sm font-medium text-gray-700 block"
                          >
                            Weekly summary
                          </label>
                          <p className="text-xs text-gray-500 mt-1">
                            Receive a weekly summary of your newsletter
                            performance and activity
                          </p>
                        </div>
                        <input
                          id="weeklySummary"
                          type="checkbox"
                          checked={
                            localPreferences?.notification_preferences.weekly_summary || false
                          }
                          onChange={(e) =>
                            handleLocalPreferenceChange({
                              notification_preferences: {
                                weekly_summary: e.target.checked,
                              },
                            })
                          }
                          disabled={isUpdatingPreferences}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Email Preferences */}
                <Card className="hover:shadow-md transition-shadow duration-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Mail className="w-5 h-5 text-blue-600" />
                      Email Settings
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label
                          htmlFor="subjectTemplate"
                          className="block text-sm font-medium text-gray-700 mb-1"
                        >
                          Default Subject Template
                        </label>
                        <Input
                          id="subjectTemplate"
                          type="text"
                          value={
                            localPreferences?.email_preferences
                              .default_subject_template || ""
                          }
                          onChange={(e) =>
                            handleLocalPreferenceChange({
                              email_preferences: {
                                default_subject_template: e.target.value,
                              },
                            })
                          }
                          disabled={isUpdatingPreferences}
                          placeholder="{title} - Weekly Newsletter"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Template for email subject lines. Use {"{title}"} as a
                          placeholder for the newsletter title.
                        </p>
                      </div>

                      <div className="space-y-4">
                        <div className="flex items-start">
                          <div className="flex items-center h-5">
                            <input
                              id="includePreviewText"
                              type="checkbox"
                              checked={
                                localPreferences?.email_preferences
                                  .include_preview_text || false
                              }
                              onChange={(e) =>
                                handleLocalPreferenceChange({
                                  email_preferences: {
                                    include_preview_text: e.target.checked,
                                  },
                                })
                              }
                              disabled={isUpdatingPreferences}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                          </div>
                          <div className="ml-3">
                            <label
                              htmlFor="includePreview"
                              className="text-sm font-medium text-gray-700"
                            >
                              Include preview text
                            </label>
                            <p className="text-xs text-gray-500 mt-1">
                              Show a brief preview of the newsletter content in
                              email clients
                            </p>
                          </div>
                        </div>

                        <div className="flex items-start">
                          <div className="flex items-center h-5">
                            <input
                              id="trackOpens"
                              type="checkbox"
                              checked={
                                localPreferences?.email_preferences.track_opens || false
                              }
                              onChange={(e) =>
                                handleLocalPreferenceChange({
                                  email_preferences: {
                                    track_opens: e.target.checked,
                                  },
                                })
                              }
                              disabled={isUpdatingPreferences}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                          </div>
                          <div className="ml-3">
                            <label
                              htmlFor="trackOpens"
                              className="text-sm font-medium text-gray-700"
                            >
                              Track email opens
                            </label>
                            <p className="text-xs text-gray-500 mt-1">
                              Monitor when recipients open your newsletters
                              (uses a small tracking pixel)
                            </p>
                          </div>
                        </div>

                        <div className="flex items-start">
                          <div className="flex items-center h-5">
                            <input
                              id="trackClicks"
                              type="checkbox"
                              checked={
                                localPreferences?.email_preferences.track_clicks || false
                              }
                              onChange={(e) =>
                                handleLocalPreferenceChange({
                                  email_preferences: {
                                    track_clicks: e.target.checked,
                                  },
                                })
                              }
                              disabled={isUpdatingPreferences}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                          </div>
                          <div className="ml-3">
                            <label
                              htmlFor="trackClicks"
                              className="text-sm font-medium text-gray-700"
                            >
                              Track link clicks
                            </label>
                            <p className="text-xs text-gray-500 mt-1">
                              Monitor which links recipients click in your
                              newsletters
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Save Changes Button */}
                {hasUnsavedChanges && (
                  <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-300 sticky bottom-4 shadow-lg z-10">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                          <p className="text-sm font-medium text-gray-900">
                            You have unsaved changes
                          </p>
                        </div>
                        <div className="flex gap-3">
                          <Button
                            variant="outline"
                            onClick={handleDiscardChanges}
                            disabled={isUpdatingPreferences}
                            className="text-sm"
                          >
                            Discard
                          </Button>
                          <Button
                            onClick={handleSavePreferences}
                            disabled={isUpdatingPreferences}
                            className="text-sm bg-blue-600 hover:bg-blue-700"
                          >
                            {isUpdatingPreferences ? "Saving..." : "Save Changes"}
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Reset Preferences */}
                <Card className="hover:shadow-md transition-shadow duration-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings className="w-5 h-5 text-gray-600" />
                      Reset Preferences
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                      <div>
                        <p className="text-sm text-gray-600">
                          Reset all preferences to their default values. This
                          action cannot be undone.
                        </p>
                      </div>
                      <div className="flex justify-end">
                        <Button
                          variant="outline"
                          onClick={() => setShowResetDialog(true)}
                          disabled={isUpdatingPreferences}
                          className="flex items-center gap-2"
                        >
                          <RotateCcw className="w-4 h-4" />
                          Reset to Defaults
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Danger Zone Card */}
                <Card className="border-red-200 hover:shadow-md transition-shadow duration-200">
                  <CardHeader>
                    <CardTitle className="text-red-600 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Danger Zone
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 mb-1">
                          Delete Account
                        </h3>
                        <p className="text-sm text-gray-600 mb-4">
                          Once you delete your account, there is no going back.
                          This action will permanently delete your account and
                          all associated data including sources, newsletters,
                          and feedback.
                        </p>
                      </div>
                      <div className="flex justify-end">
                        <Button
                          variant="outline"
                          onClick={() => setShowDeleteDialog(true)}
                          className="border-red-300 text-red-600 hover:bg-red-50 flex items-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          Delete Account
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )
        )}
      </main>

      {/* Reset Preferences Dialog */}
      <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-gray-600" />
              Reset Preferences
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to reset all preferences to their default
              values? This will restore all settings to their original state.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowResetDialog(false)}
              disabled={isUpdatingPreferences}
            >
              Cancel
            </Button>
            <Button
              onClick={handleResetPreferences}
              disabled={isUpdatingPreferences}
            >
              {isUpdatingPreferences ? "Resetting..." : "Reset to Defaults"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Delete Account
            </DialogTitle>
            <DialogDescription>
              Are you absolutely sure you want to delete your account? This
              action cannot be undone. All your data including sources,
              newsletters, and feedback will be permanently deleted.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleDeleteAccount}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {isDeleting ? "Deleting..." : "Yes, Delete My Account"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
