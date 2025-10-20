import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import apiClient from "../services/api";
import { Navigation } from "../components/Navigation";
import { Button } from "../components/ui/Button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/Card";
import { Textarea } from "../components/ui/Textarea";
import { Input } from "../components/ui/Input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/Dialog";
import { FeedbackButtons } from "../components/FeedbackButtons";
import {
  ArrowLeft,
  Save,
  Send,
  RefreshCw,
  Loader2,
  Edit2,
  Trash2,
  Mail,
  AlertTriangle,
} from "lucide-react";

interface DraftSection {
  id: string;
  type: string;
  title?: string;
  content: string;
  source_ids: string[];
  metadata: any;
}

interface Draft {
  id: string;
  user_id: string;
  title: string;
  sections: DraftSection[];
  status: string;
  metadata: any;
  generated_at: string;
  published_at?: string;
  email_sent: boolean;
}

interface Feedback {
  id: string;
  user_id: string;
  newsletter_id: string;
  section_id: string;
  feedback_type: "thumbs_up" | "thumbs_down" | null;
  comment: string;
}

type FeedbackResponseMap = {
  [key: string]: Feedback;
};

export default function DraftReview() {
  const { draftId } = useParams<{ draftId: string }>();
  const navigate = useNavigate();

  const [draft, setDraft] = useState<Draft | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [showPublishDialog, setShowPublishDialog] = useState(false);
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackResponseMap>({});
  const feedbackFetchedRef = useRef<string | null>(null);

  // Memoized fetchFeedback function
  const fetchFeedback = useCallback(async (newsletterId: string) => {
    // Prevent duplicate fetches for the same draft
    if (feedbackFetchedRef.current === newsletterId) return;

    try {
      feedbackFetchedRef.current = newsletterId;
      const response = await apiClient.get(
        `/api/feedback/newsletter/${newsletterId}`
      );

      const feedbackMap: FeedbackResponseMap = {};
      if (response.data.feedback && Array.isArray(response.data.feedback)) {
        response.data.feedback.forEach((feedbackItem: any) => {
          if (feedbackItem.section_id) {
            feedbackMap[feedbackItem.section_id] = feedbackItem;
          }
        });
      }

      setFeedback(feedbackMap);
    } catch (err: any) {
      console.error("Failed to fetch feedback:", err);
      setError(err.response?.data?.detail || "Failed to fetch feedback");
      feedbackFetchedRef.current = null; // Reset on error to allow retry
    }
  }, []);

  // Memoized fetchDraft function
  const fetchDraft = useCallback(async () => {
    try {
      setLoading(true);
      setError(""); // Clear any previous errors
      const response = await apiClient.get(`/api/drafts/${draftId}`);
      
      setDraft((prevDraft) => {
        // If draft just finished generating, show success message and fetch feedback
        if (prevDraft?.status === "generating" && response.data.status === "ready") {
          setSuccessMessage("Draft generated successfully!");
          setTimeout(() => setSuccessMessage(""), 3000);
          // Reset feedback tracking to allow fresh fetch
          feedbackFetchedRef.current = null;
          fetchFeedback(response.data.id);
        }
        return response.data;
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to fetch draft");
      setFeedback({}); // Clear feedback state on error
      feedbackFetchedRef.current = null; // Reset feedback tracking on error
    } finally {
      setLoading(false);
    }
  }, [draftId, fetchFeedback]);

  // Initial fetch on mount or when draftId changes
  useEffect(() => {
    if (draftId) {
      feedbackFetchedRef.current = null; // Reset feedback tracking for new draft
      setFeedback({}); // Clear feedback state for new draft
      fetchDraft();
    }

    // Cleanup function to reset state when draftId changes or component unmounts
    return () => {
      setFeedback({});
      feedbackFetchedRef.current = null;
    };
  }, [draftId, fetchDraft]);

  // Poll for draft completion if status is 'generating'
  useEffect(() => {
    if (draft?.status === "generating") {
      const pollInterval = setInterval(() => {
        fetchDraft();
      }, 10000); // Poll every 10 seconds

      return () => clearInterval(pollInterval);
    }
  }, [draft?.status, fetchDraft]);

  // Fetch feedback when draft becomes ready
  useEffect(() => {
    if (!draftId || !draft) return;
    if (draft.status === "generating") return;

    fetchFeedback(draftId);
  }, [draftId, draft?.id, draft?.status]); // Removed fetchFeedback from dependencies

  const handleSave = async () => {
    if (!draft) return;

    try {
      setSaving(true);
      setError("");

      await apiClient.put(`/api/drafts/${draftId}`, {
        title: draft.title,
        sections: draft.sections,
        metadata: draft.metadata,
      });

      setSuccessMessage("Draft saved successfully");
      setEditMode(false);
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save draft");
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!draft) return;

    try {
      setPublishing(true);
      setError("");
      setShowPublishDialog(false);

      await apiClient.post(`/api/drafts/${draftId}/publish`, {
        send_email: true,
        recipient_emails: null,
        subject: draft.title,
      });

      setSuccessMessage("Draft published and email queued for delivery!");
      fetchDraft(); // Refresh to show updated status
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to publish draft");
    } finally {
      setPublishing(false);
    }
  };

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      setError("");
      setShowRegenerateDialog(false);

      const response = await apiClient.post(
        `/api/drafts/${draftId}/regenerate`,
        {
          topic_count: null,
          use_voice_profile: true,
        }
      );

      if (response.data.status === "ready") {
        // Successfully regenerated, navigate to new draft
        setSuccessMessage("Draft regenerated successfully!");
        setTimeout(() => {
          navigate(`/drafts/${response.data.draft_id}`);
        }, 500);
      } else if (response.data.status === "failed") {
        // Regeneration failed
        setError(
          response.data.error ||
            response.data.message ||
            "Failed to regenerate draft"
        );
      } else if (response.data.status === "generating") {
        setSuccessMessage("Draft regenerated successfully!");
        setTimeout(() => {
          navigate(`/drafts/${response.data.draft_id}`);
        }, 500);
      } else {
        // Unknown status
        setError(`Unexpected status: ${response.data.status}`);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to regenerate draft"
      );
    } finally {
      setRegenerating(false);
    }
  };

  const handleDelete = async () => {
    try {
      setShowDeleteDialog(false);
      await apiClient.delete(`/api/drafts/${draftId}`);
      navigate("/drafts");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete draft");
    }
  };

  const updateSection = (sectionId: string, field: string, value: string) => {
    if (!draft) return;

    setDraft({
      ...draft,
      sections: draft.sections.map((section) =>
        section.id === sectionId ? { ...section, [field]: value } : section
      ),
    });
  };

  const renderSection = (section: DraftSection) => {
    if (editMode) {
      return (
        <div key={section.id} className="mb-6">
          {section.type === "topic" && (
            <Input
              value={section.title || ""}
              onChange={(e) =>
                updateSection(section.id, "title", e.target.value)
              }
              className="mb-2 text-lg font-semibold"
              placeholder="Section title"
            />
          )}
          <Textarea
            value={section.content}
            onChange={(e) =>
              updateSection(section.id, "content", e.target.value)
            }
            className="min-h-[150px] font-sans"
            placeholder="Section content"
          />
        </div>
      );
    }

    return (
      <div key={section.id} className="mb-8">
        {section.type === "intro" && (
          <div className="prose max-w-none">
            <p className="text-gray-700 leading-relaxed">{section.content}</p>
            <div className="mt-3 flex items-center justify-between">
              <FeedbackButtons
                newsletterId={draft!.id}
                sectionId={section.id}
                size="sm"
                selectedFeedbackType={
                  feedback?.[section.id]?.feedback_type || null
                }
                onFeedbackSubmitted={() => {
                  feedbackFetchedRef.current = null;
                  fetchFeedback(draft!.id);
                }}
              />
            </div>
          </div>
        )}
        {section.type === "topic" && (
          <div className="border-l-4 border-indigo-500 pl-6">
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-xl font-semibold text-gray-900">
                {section.title}
              </h3>
              <FeedbackButtons
                newsletterId={draft!.id}
                sectionId={section.id}
                size="sm"
                selectedFeedbackType={
                  feedback?.[section.id]?.feedback_type || null
                }
                onFeedbackSubmitted={() => {
                  feedbackFetchedRef.current = null;
                  fetchFeedback(draft!.id);
                }}
              />
            </div>
            <div className="prose max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {section.content}
              </p>
            </div>
          </div>
        )}
        {section.type === "conclusion" && (
          <div className="mt-8 pt-6 border-t-2 border-gray-200">
            <div className="prose max-w-none">
              <p className="text-gray-700 leading-relaxed">{section.content}</p>
            </div>
            <div className="mt-3 flex items-center justify-between">
              <FeedbackButtons
                newsletterId={draft!.id}
                sectionId={section.id}
                size="sm"
                selectedFeedbackType={
                  feedback?.[section.id]?.feedback_type || null
                }
                onFeedbackSubmitted={() => {
                  feedbackFetchedRef.current = null;
                  fetchFeedback(draft!.id);
                }}
              />
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Draft not found
          </h2>
          <Button onClick={() => navigate("/drafts")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Drafts
          </Button>
        </div>
      </div>
    );
  }

  const isPublished = draft.status === "published";

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Navigation currentPage="Drafts" />
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate("/drafts")}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Drafts
          </Button>

          <div className="flex items-start justify-between mb-4">
            {editMode ? (
              <Input
                value={draft.title}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setDraft({ ...draft, title: e.target.value })
                }
                className="text-3xl font-bold flex-1 mr-4"
              />
            ) : (
              <h1 className="text-3xl font-bold text-gray-900 flex-1">
                {draft.title}
              </h1>
            )}
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                draft.status === "published"
                  ? "bg-purple-100 text-purple-800"
                  : draft.status === "editing"
                  ? "bg-blue-100 text-blue-800"
                  : "bg-green-100 text-green-800"
              }`}
            >
              {draft.status}
            </span>
            {draft.metadata.topic_count && (
              <span>{draft.metadata.topic_count} topics</span>
            )}
            {draft.metadata.estimated_read_time && (
              <span>• {draft.metadata.estimated_read_time} read</span>
            )}
            {draft.email_sent && (
              <span className="flex items-center gap-1 text-green-600">
                <Mail className="h-4 w-4" />
                Email sent
              </span>
            )}
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
            {successMessage}
          </div>
        )}

        {/* Generating status */}
        {draft.status === "generating" && (
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
            <div className="flex items-center">
              <Loader2 className="h-5 w-5 text-blue-500 mr-3 animate-spin" />
              <div>
                <h3 className="text-sm font-medium text-blue-800">
                  Generating Draft...
                </h3>
                <p className="mt-1 text-sm text-blue-700">
                  Your newsletter is being generated. This may take 10-30
                  seconds. The page will automatically update when ready.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Warning for fallback/empty drafts */}
        {draft.metadata?.no_content && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-yellow-400 mr-3 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-yellow-800">
                  No Content Available
                </h3>
                <p className="mt-1 text-sm text-yellow-700">
                  This draft is empty because no content was found from your
                  sources. Please connect content sources and crawl them, then
                  regenerate this draft.
                </p>
              </div>
            </div>
          </div>
        )}

        {draft.metadata?.fallback && !draft.metadata?.no_content && (
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-blue-400 mr-3 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-blue-800">
                  Limited Content
                </h3>
                <p className="mt-1 text-sm text-blue-700">
                  No trending topics were detected. This draft shows recent
                  content summaries instead. For better results, ensure your
                  sources have diverse, recent content.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 mb-8 flex-wrap">
          {!isPublished && (
            <>
              <Button
                onClick={() => {
                  if (editMode) {
                    handleSave();
                  } else {
                    setEditMode(true);
                  }
                }}
                disabled={saving}
                variant={editMode ? "primary" : "outline"}
                className={editMode ? "bg-indigo-600 hover:bg-indigo-700" : ""}
              >
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : editMode ? (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Save Changes
                  </>
                ) : (
                  <>
                    <Edit2 className="mr-2 h-4 w-4" />
                    Edit
                  </>
                )}
              </Button>

              {editMode && (
                <Button
                  onClick={() => {
                    setEditMode(false);
                    fetchDraft(); // Reset changes
                  }}
                  variant="outline"
                >
                  Cancel
                </Button>
              )}

              <Button
                onClick={() => setShowPublishDialog(true)}
                disabled={publishing || editMode}
                className="bg-green-600 hover:bg-green-700"
              >
                {publishing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Publishing...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Publish & Send
                  </>
                )}
              </Button>
            </>
          )}

          <Button
            onClick={() => setShowRegenerateDialog(true)}
            disabled={regenerating || editMode}
            variant="outline"
          >
            {regenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Regenerating...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Regenerate
              </>
            )}
          </Button>

          <Button
            onClick={() => setShowDeleteDialog(true)}
            disabled={editMode}
            variant="outline"
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>

        {/* Draft Content */}
        <Card>
          <CardContent className="pt-6">
            {draft.sections.map((section) => renderSection(section))}
          </CardContent>
        </Card>

        {/* Metadata */}
        {draft.metadata.trends_used &&
          draft.metadata.trends_used.length > 0 && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="text-lg">Trends Included</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {draft.metadata.trends_used.map(
                    (trend: string, index: number) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm"
                      >
                        {trend}
                      </span>
                    )
                  )}
                </div>
              </CardContent>
            </Card>
          )}
      </div>

      {/* Publish Confirmation Dialog */}
      <Dialog open={showPublishDialog} onOpenChange={setShowPublishDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Send className="w-5 h-5 text-green-600" />
              Publish & Send Newsletter
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to publish this draft? It will be sent to
              your email address. This action will mark the draft as published.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowPublishDialog(false)}
              disabled={publishing}
            >
              Cancel
            </Button>
            <Button
              onClick={handlePublish}
              disabled={publishing}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {publishing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Publishing...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Yes, Publish & Send
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Regenerate Confirmation Dialog */}
      <Dialog
        open={showRegenerateDialog}
        onOpenChange={setShowRegenerateDialog}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              Regenerate Draft
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to regenerate this draft? Your current edits
              will be lost and a new draft will be created with fresh content.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRegenerateDialog(false)}
              disabled={regenerating}
            >
              Cancel
            </Button>
            <Button
              onClick={handleRegenerate}
              disabled={regenerating}
              className="bg-orange-600 hover:bg-orange-700 text-white"
            >
              {regenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Regenerating...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Yes, Regenerate
                </>
              )}
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
              Delete Draft
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this draft? This action cannot be
              undone. The draft will be permanently removed from your account.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Yes, Delete Draft
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
