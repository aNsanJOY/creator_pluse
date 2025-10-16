import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card";
import { AlertCircle, CheckCircle, Clock, Zap, TrendingUp } from "lucide-react";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Global cache to prevent duplicate requests across component instances
let cachedUsage: any = null;
let lastFetchTime = 0;
const CACHE_DURATION = 60000; // 1 minute cache

interface LLMUsageSummary {
  today: {
    calls: number;
    tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
  this_month: {
    calls: number;
    tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
  rate_limits: {
    per_minute: {
      can_call: boolean;
      current_count: number;
      limit_value: number;
      remaining: number;
      reset_at: string;
    };
    per_day: {
      can_call: boolean;
      current_count: number;
      limit_value: number;
      remaining: number;
      reset_at: string;
    };
  };
}

export function LLMUsageCard() {
  const [usage, setUsage] = useState<LLMUsageSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUsage();
    // Refresh every 2 minutes (less frequent to reduce API calls)
    const interval = setInterval(fetchUsage, 120000);
    return () => clearInterval(interval);
  }, []);

  const fetchUsage = async () => {
    try {
      const now = Date.now();
      
      // Use cached data if available and fresh
      if (cachedUsage && (now - lastFetchTime) < CACHE_DURATION) {
        console.log("Using cached LLM usage data");
        setUsage(cachedUsage);
        setError(null);
        setLoading(false);
        return;
      }
      
      console.log("Fetching fresh LLM usage data...");
      const token = localStorage.getItem("access_token");
      const response = await axios.get(`${API_URL}/api/llm/usage/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log("LLM Usage Response:", response.data);
      
      // Update cache
      cachedUsage = response.data.summary;
      lastFetchTime = now;
      
      setUsage(response.data.summary);
      setError(null);
    } catch (err: any) {
      console.error("Failed to fetch LLM usage:", err);
      setError("Failed to load usage data");
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const getPercentageColor = (percentage: number) => {
    if (percentage >= 90) return "text-red-600";
    if (percentage >= 70) return "text-yellow-600";
    return "text-green-600";
  };

  const getProgressBarColor = (percentage: number) => {
    if (percentage >= 90) return "bg-red-500";
    if (percentage >= 70) return "bg-yellow-500";
    return "bg-green-500";
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-purple-600" />
            LLM API Usage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !usage) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-purple-600" />
            LLM API Usage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error || "Failed to load"}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const minutePercentage =
    usage.rate_limits.per_minute.limit_value > 0
      ? (usage.rate_limits.per_minute.current_count /
          usage.rate_limits.per_minute.limit_value) *
        100
      : 0;
  const dayPercentage =
    usage.rate_limits.per_day.limit_value > 0
      ? (usage.rate_limits.per_day.current_count /
          usage.rate_limits.per_day.limit_value) *
        100
      : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-purple-600" />
          LLM API Usage
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Rate Limits */}
        <div className="space-y-3">
          {/* Per Minute Limit */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">
                  Per Minute
                </span>
              </div>
              <div className="flex items-center gap-2">
                {usage.rate_limits.per_minute.can_call ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-600" />
                )}
                <span
                  className={`text-sm font-bold ${getPercentageColor(
                    minutePercentage
                  )}`}
                >
                  {usage.rate_limits.per_minute.remaining} remaining
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
              <span>{usage.rate_limits.per_minute.limit_value} calls</span>
              <span>{minutePercentage.toFixed(0)}% used</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${getProgressBarColor(
                  minutePercentage
                )}`}
                style={{ width: `${Math.min(minutePercentage, 100)}%` }}
              />
            </div>
          </div>

          {/* Per Day Limit */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">
                  Per Day
                </span>
              </div>
              <div className="flex items-center gap-2">
                {usage.rate_limits.per_day.can_call ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-600" />
                )}
                <span
                  className={`text-sm font-bold ${getPercentageColor(
                    dayPercentage
                  )}`}
                >
                  {formatNumber(usage.rate_limits.per_day.remaining)} remaining
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
              <span>
                {formatNumber(usage.rate_limits.per_day.limit_value)} calls
              </span>
              <span>{dayPercentage.toFixed(1)}% used</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${getProgressBarColor(
                  dayPercentage
                )}`}
                style={{ width: `${Math.min(dayPercentage, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Usage Stats */}
        <div className="border-t border-gray-200 pt-3 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Today's Calls</span>
            <span className="font-medium text-gray-900">
              {usage.today.calls}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Today's Tokens</span>
            <span className="font-medium text-gray-900">
              {formatNumber(usage.today.tokens)}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Monthly Calls</span>
            <span className="font-medium text-gray-900">
              {formatNumber(usage.this_month.calls)}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Monthly Tokens</span>
            <span className="font-medium text-gray-900">
              {formatNumber(usage.this_month.tokens)}
            </span>
          </div>
        </div>

        {/* Warning if near limit */}
        {(dayPercentage >= 80 || minutePercentage >= 80) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5" />
              <div className="text-xs text-yellow-800">
                <p className="font-medium">Approaching Rate Limit</p>
                <p className="mt-1">
                  You're using{" "}
                  {Math.max(dayPercentage, minutePercentage).toFixed(0)}% of
                  your LLM API quota. Consider optimizing your usage or
                  upgrading your plan.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error if limit exceeded */}
        {(!usage.rate_limits.per_minute.can_call ||
          !usage.rate_limits.per_day.can_call) && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 mt-0.5" />
              <div className="text-xs text-red-800">
                <p className="font-medium">Rate Limit Exceeded</p>
                <p className="mt-1">
                  You've reached your LLM API limit. Please wait for the counter
                  to reset.
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
