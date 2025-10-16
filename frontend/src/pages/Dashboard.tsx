import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Button } from "../components/ui/Button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/Card";
import {
  LogOut,
  User,
  Sparkles,
  Rss,
  FileText,
  TrendingUp,
  Send,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Clock,
  Calendar,
} from "lucide-react";
import axios from "axios";
import { LLMUsageCard } from "../components/LLMUsageCard";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface DashboardStats {
  sources: {
    total: number;
    active: number;
    by_type: Record<string, number>;
  };
  drafts: {
    total: number;
    published: number;
    pending: number;
    emails_sent: number;
  };
  content: {
    total_items: number;
    trends_detected: number;
  };
  voice: {
    samples_uploaded: number;
    profile_trained: boolean;
  };
  email: {
    sent_30d: number;
    failed_30d: number;
    rate_limit: {
      can_send: boolean;
      current_count: number;
      daily_limit: number;
      remaining: number;
    };
  };
}

interface RecentDraft {
  id: string;
  title: string;
  status: string;
  generated_at: string;
  published_at?: string;
  email_sent: boolean;
}

interface CrawlStatus {
  sources: Array<{
    id: string;
    name: string;
    type: string;
    status: string;
    last_crawled_at: string | null;
    error_message: string | null;
    latest_crawl: any;
  }>;
  total: number;
  active: number;
  error: number;
  last_batch_crawl_at: string | null;
  next_scheduled_crawl_at: string | null;
  is_crawling: boolean;
  last_crawl_duration_seconds: number | null;
  sources_crawled_count: number;
  sources_failed_count: number;
}

export function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentDrafts, setRecentDrafts] = useState<RecentDraft[]>([]);
  const [crawlStatus, setCrawlStatus] = useState<CrawlStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggeringCrawl, setTriggeringCrawl] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token");

      const [statsRes, draftsRes, crawlRes] = await Promise.all([
        axios.get(`${API_URL}/api/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_URL}/api/dashboard/recent-drafts?limit=5`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios
          .get(`${API_URL}/api/crawl/status`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          .catch(() => ({
            data: {
              last_crawled_at: null,
              next_scheduled_at: null,
              is_crawling: false,
            },
          })),
      ]);

      setStats(statsRes.data.stats);
      setRecentDrafts(draftsRes.data.drafts);
      setCrawlStatus(crawlRes.data);
      setError(null);
    } catch (err: any) {
      console.error("Failed to fetch dashboard data:", err);
      setError("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerCrawl = async () => {
    try {
      setTriggeringCrawl(true);
      const token = localStorage.getItem("access_token");

      await axios.post(
        `${API_URL}/api/crawl/trigger`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      // Refresh crawl status
      const crawlRes = await axios.get(`${API_URL}/api/crawl/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCrawlStatus(crawlRes.data);
    } catch (err: any) {
      console.error("Failed to trigger crawl:", err);
      alert(err.response?.data?.detail || "Failed to trigger crawl");
    } finally {
      setTriggeringCrawl(false);
    }
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getLastCrawledTime = () => {
    // Use batch crawl time from the schedule
    return crawlStatus?.last_batch_crawl_at || null;
  };

  const getNextScheduledTime = () => {
    // Use next scheduled crawl time from the schedule
    return crawlStatus?.next_scheduled_crawl_at || null;
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">CreatorPulse</h1>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="flex items-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back{user?.full_name ? `, ${user.full_name}` : ""}!
          </h2>
          <p className="text-gray-600">
            Your newsletter dashboard is ready to help you create amazing
            content.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-600">Loading dashboard...</div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-red-800">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Sources Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Rss className="w-4 h-4 text-blue-600" />
                    Sources
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-gray-900">
                    {stats?.sources.active || 0}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {stats?.sources.total || 0} total connected
                  </p>
                </CardContent>
              </Card>

              {/* Drafts Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <FileText className="w-4 h-4 text-purple-600" />
                    Drafts
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-gray-900">
                    {stats?.drafts.pending || 0}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {stats?.drafts.published || 0} published
                  </p>
                </CardContent>
              </Card>

              {/* Content Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <TrendingUp className="w-4 h-4 text-green-600" />
                    Content
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-gray-900">
                    {stats?.content.total_items || 0}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {stats?.content.trends_detected || 0} trends detected
                  </p>
                </CardContent>
              </Card>

              {/* Emails Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Send className="w-4 h-4 text-indigo-600" />
                    Emails (30d)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-gray-900">
                    {stats?.email.sent_30d || 0}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {stats?.email.rate_limit.remaining || 0} remaining today
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Recent Drafts Card */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Recent Drafts</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate("/drafts")}
                    >
                      View All
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {recentDrafts.length === 0 ? (
                    <p className="text-sm text-gray-600">
                      No drafts yet. Generate your first draft!
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {recentDrafts.map((draft) => (
                        <div
                          key={draft.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                          onClick={() => navigate(`/drafts/${draft.id}`)}
                        >
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900 text-sm">
                              {draft.title}
                            </h4>
                            <p className="text-xs text-gray-600 mt-1">
                              {new Date(
                                draft.generated_at
                              ).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            {draft.email_sent && (
                              <Send className="w-4 h-4 text-green-600" />
                            )}
                            <span
                              className={`text-xs px-2 py-1 rounded-full ${
                                draft.status === "published"
                                  ? "bg-green-100 text-green-800"
                                  : draft.status === "editing"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-blue-100 text-blue-800"
                              }`}
                            >
                              {draft.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Actions Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => navigate("/sources")}
                  >
                    <Rss className="w-4 h-4 mr-2" />
                    Connect Sources
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => navigate("/voice-training")}
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Train Your Voice
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => navigate("/drafts")}
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    View Drafts
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => navigate("/profile")}
                  >
                    <User className="w-4 h-4 mr-2" />
                    Profile Settings
                  </Button>
                </CardContent>
              </Card>

              {/* Voice Training Status Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-600" />
                    Voice Training
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 mb-3">
                    {stats?.voice.profile_trained ? (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <span className="text-sm font-medium text-green-800">
                          Trained
                        </span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-5 h-5 text-yellow-600" />
                        <span className="text-sm font-medium text-yellow-800">
                          Not Trained
                        </span>
                      </>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-4">
                    {stats?.voice.samples_uploaded || 0} sample(s) uploaded
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => navigate("/voice-training")}
                  >
                    {stats?.voice.profile_trained
                      ? "Manage Samples"
                      : "Upload Samples"}
                  </Button>
                </CardContent>
              </Card>
              
              {/* LLM API Usage Card */}
              <LLMUsageCard />
              
              {/* Crawl Status Card */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-5 h-5 text-indigo-600" />
                      Content Crawl Status
                    </span>
                    <Button
                      size="sm"
                      onClick={handleTriggerCrawl}
                      disabled={triggeringCrawl || crawlStatus?.is_crawling}
                      className="flex items-center gap-2"
                    >
                      <RefreshCw
                        className={`w-4 h-4 ${
                          triggeringCrawl || crawlStatus?.is_crawling
                            ? "animate-spin"
                            : ""
                        }`}
                      />
                      {triggeringCrawl
                        ? "Triggering..."
                        : crawlStatus?.is_crawling
                        ? "Crawling..."
                        : "Crawl All Now"}
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between py-2 border-b border-gray-100">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">
                        All Sources Last Crawled
                      </span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {formatDateTime(getLastCrawledTime())}
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">
                        Next All Sources Crawl
                      </span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {formatDateTime(getNextScheduledTime())}
                    </span>
                  </div>
                  {crawlStatus?.is_crawling && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
                      <p className="text-xs text-blue-700 flex items-center gap-2">
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        Batch crawl in progress...
                      </p>
                    </div>
                  )}
                  {crawlStatus && crawlStatus.total > 0 && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mt-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600">Total Sources:</span>
                        <span className="font-medium text-gray-900">{crawlStatus.total}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs mt-1">
                        <span className="text-gray-600">Active:</span>
                        <span className="font-medium text-green-600">{crawlStatus.active}</span>
                      </div>
                      {crawlStatus.error > 0 && (
                        <div className="flex items-center justify-between text-xs mt-1">
                          <span className="text-gray-600">Errors:</span>
                          <span className="font-medium text-red-600">{crawlStatus.error}</span>
                        </div>
                      )}
                      {crawlStatus.last_crawl_duration_seconds && (
                        <div className="flex items-center justify-between text-xs mt-1">
                          <span className="text-gray-600">Last Duration:</span>
                          <span className="font-medium text-gray-900">{crawlStatus.last_crawl_duration_seconds}s</span>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
