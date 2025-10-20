import { useState, useEffect } from "react";
import { ThumbsUp, ThumbsDown, MessageSquare } from "lucide-react";
import { Button } from "./ui/Button";
import { Textarea } from "./ui/Textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "./ui/Dialog";
import apiClient from "../services/api";

interface FeedbackButtonsProps {
  newsletterId: string;
  sectionId?: string;
  onFeedbackSubmitted?: () => void;
  size?: "sm" | "md" | "lg";
  showCommentOption?: boolean;
  selectedFeedbackType: "thumbs_up" | "thumbs_down" | null;
  user_comment?: string;
}

export function FeedbackButtons({
  newsletterId,
  sectionId,
  onFeedbackSubmitted,
  user_comment = "",
  selectedFeedbackType = null,
  size = "sm",
  showCommentOption = true,
}: FeedbackButtonsProps) {
  const [feedbackType, setFeedbackType] = useState<
    "thumbs_up" | "thumbs_down" | null
  >(selectedFeedbackType);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [comment, setComment] = useState(user_comment);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Sync internal state with prop changes
  useEffect(() => {
    setFeedbackType(selectedFeedbackType);
  }, [selectedFeedbackType]);

  // Sync comment with prop changes
  useEffect(() => {
    setComment(user_comment);
  }, [user_comment]);

  const handleFeedback = async (
    type: "thumbs_up" | "thumbs_down",
    withComment: boolean = false
  ) => {
    if (withComment) {
      setFeedbackType(type);
      setShowCommentDialog(true);
      return;
    }

    await submitFeedback(type, "");
  };

  const submitFeedback = async (
    type: "thumbs_up" | "thumbs_down",
    commentText: string
  ) => {
    try {
      setSubmitting(true);
      setError("");

      await apiClient.post("/api/feedback", {
        newsletter_id: newsletterId,
        section_id: sectionId,
        feedback_type: type,
        comment: commentText || undefined,
      });

      setFeedbackType(type);
      setShowCommentDialog(false);
      setComment("");

      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to submit feedback");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCommentSubmit = async () => {
    if (!feedbackType) return;
    await submitFeedback(feedbackType, comment);
  };

  const buttonSize =
    size === "sm" ? "h-8 w-8" : size === "md" ? "h-10 w-10" : "h-12 w-12";
  const iconSize = size === "sm" ? 16 : size === "md" ? 20 : 24;

  return (
    <>
      <div className="flex items-center gap-2">
        <Button
          variant={feedbackType === "thumbs_up" ? "primary" : "outline"}
          size={size}
          className={buttonSize}
          onClick={() => handleFeedback("thumbs_up")}
          disabled={submitting}
          title="This is helpful"
        >
          <ThumbsUp size={iconSize} />
        </Button>

        <Button
          variant={feedbackType === "thumbs_down" ? "destructive" : "outline"}
          size={size}
          className={buttonSize}
          onClick={() => handleFeedback("thumbs_down")}
          disabled={submitting}
          title="This needs improvement"
        >
          <ThumbsDown size={iconSize} />
        </Button>

        {showCommentOption && (
          <Button
            variant="ghost"
            size={size}
            className={buttonSize}
            onClick={() => {
              setFeedbackType(feedbackType || "thumbs_up");
              setShowCommentDialog(true);
            }}
            disabled={submitting}
            title="Add comment"
          >
            <MessageSquare size={iconSize} />
          </Button>
        )}
      </div>

      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}

      <Dialog open={showCommentDialog} onOpenChange={setShowCommentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Feedback Comment</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                How can we improve this {sectionId ? "section" : "draft"}?
              </label>
              <Textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Share your thoughts..."
                rows={4}
                className="w-full"
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCommentDialog(false);
                setComment("");
                setError("");
              }}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCommentSubmit}
              disabled={submitting || !comment.trim()}
            >
              {submitting ? "Submitting..." : "Submit Feedback"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
