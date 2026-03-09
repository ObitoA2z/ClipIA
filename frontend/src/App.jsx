import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import AdminRoute from "./components/AdminRoute";
import BottomNav from "./components/BottomNav";
import CommandPalette from "./components/CommandPalette";
import FeedbackWidget from "./components/FeedbackWidget";
import Footer from "./components/Footer";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import Spinner from "./components/ui/Spinner";
import useAuth from "./hooks/useAuth";

const AdminAnalytics = lazy(() => import("./pages/admin/AdminAnalytics"));
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const AdminLayout = lazy(() => import("./pages/admin/AdminLayout"));
const AdminPipeline = lazy(() => import("./pages/admin/AdminPipeline"));
const AdminSettings = lazy(() => import("./pages/admin/AdminSettings"));
const AdminTools = lazy(() => import("./pages/admin/AdminTools"));
const AdminUsers = lazy(() => import("./pages/admin/AdminUsers"));
const AICoachPage = lazy(() => import("./pages/AICoachPage"));
const ClipEditor = lazy(() => import("./pages/ClipEditor"));
const ContentHub = lazy(() => import("./pages/ContentHub"));
const CreatorAnalytics = lazy(() => import("./pages/CreatorAnalytics"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const Home = lazy(() => import("./pages/Home"));
const Login = lazy(() => import("./pages/Login"));
const Pricing = lazy(() => import("./pages/Pricing"));
const Profile = lazy(() => import("./pages/Profile"));
const Privacy = lazy(() => import("./pages/Privacy"));
const ReferralPage = lazy(() => import("./pages/ReferralPage"));
const Register = lazy(() => import("./pages/Register"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const Scheduler = lazy(() => import("./pages/Scheduler"));
const TeamSettings = lazy(() => import("./pages/TeamSettings"));
const Terms = lazy(() => import("./pages/Terms"));
const VideoDetail = lazy(() => import("./pages/VideoDetail"));

const AUTH_LAYOUT_PREFIXES = [
  "/dashboard",
  "/profile",
  "/analytics",
  "/scheduler",
  "/team",
  "/referral",
  "/video",
  "/clip-editor",
  "/ai-coach",
  "/content-hub",
  "/admin",
];

function PageFallback() {
  return (
    <div className="ui-card" style={{ display: "grid", placeItems: "center", minHeight: 240 }}>
      <Spinner size={24} />
      <p className="muted" style={{ marginTop: 12 }}>
        Chargement de l'interface...
      </p>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route
        path="/referral"
        element={(
          <ProtectedRoute>
            <ReferralPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/scheduler"
        element={(
          <ProtectedRoute>
            <Scheduler />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/team"
        element={(
          <ProtectedRoute>
            <TeamSettings />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/dashboard"
        element={(
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/profile"
        element={(
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/analytics"
        element={(
          <ProtectedRoute>
            <CreatorAnalytics />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/video/:videoId"
        element={(
          <ProtectedRoute>
            <VideoDetail />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/clip-editor/:clipId"
        element={(
          <ProtectedRoute>
            <ClipEditor />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/ai-coach"
        element={(
          <ProtectedRoute>
            <AICoachPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/content-hub/:videoId"
        element={(
          <ProtectedRoute>
            <ContentHub />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/admin"
        element={(
          <AdminRoute>
            <AdminLayout />
          </AdminRoute>
        )}
      >
        <Route index element={<AdminDashboard />} />
        <Route path="users" element={<AdminUsers />} />
        <Route path="pipeline" element={<AdminPipeline />} />
        <Route path="analytics" element={<AdminAnalytics />} />
        <Route path="settings" element={<AdminSettings />} />
        <Route path="tools" element={<AdminTools />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function CustomCursor() {
  const [position, setPosition] = useState({ x: -100, y: -100 });

  useEffect(() => {
    const onMouseMove = (event) => {
      setPosition({ x: event.clientX, y: event.clientY });
    };
    window.addEventListener("mousemove", onMouseMove);
    return () => window.removeEventListener("mousemove", onMouseMove);
  }, []);

  return (
    <>
      <span className="custom-cursor-ring" style={{ left: position.x, top: position.y }} />
      <span className="custom-cursor" style={{ left: position.x, top: position.y }} />
    </>
  );
}

function App() {
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const [paletteOpen, setPaletteOpen] = useState(false);

  const isAuthLayout = useMemo(() => {
    if (!isAuthenticated) {
      return false;
    }
    return AUTH_LAYOUT_PREFIXES.some(
      (prefix) => location.pathname === prefix || location.pathname.startsWith(`${prefix}/`),
    );
  }, [isAuthenticated, location.pathname]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <div className="app-shell">
      {!isAuthLayout ? <Navbar /> : null}
      {isAuthLayout ? (
        <main className="main-content main-content-auth">
          <div className="app-layout">
            <Sidebar />
            <section style={{ padding: "20px 0 100px 0" }}>
              <Suspense fallback={<PageFallback />}>
                <AppRoutes />
              </Suspense>
            </section>
          </div>
          <BottomNav />
        </main>
      ) : (
        <main className="main-content">
          <Suspense fallback={<PageFallback />}>
            <AppRoutes />
          </Suspense>
        </main>
      )}
      <FeedbackWidget />
      {!isAuthLayout ? <Footer /> : null}
      {isAuthenticated ? <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} /> : null}
      <CustomCursor />
    </div>
  );
}

export default App;
