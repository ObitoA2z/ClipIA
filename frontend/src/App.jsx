import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";

import AdminRoute from "./components/AdminRoute";
import FeedbackWidget from "./components/FeedbackWidget";
import Footer from "./components/Footer";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Spinner from "./components/ui/Spinner";

const AdminAnalytics = lazy(() => import("./pages/admin/AdminAnalytics"));
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const AdminLayout = lazy(() => import("./pages/admin/AdminLayout"));
const AdminPipeline = lazy(() => import("./pages/admin/AdminPipeline"));
const AdminSettings = lazy(() => import("./pages/admin/AdminSettings"));
const AdminTools = lazy(() => import("./pages/admin/AdminTools"));
const AdminUsers = lazy(() => import("./pages/admin/AdminUsers"));
const ClipEditor = lazy(() => import("./pages/ClipEditor"));
const CreatorAnalytics = lazy(() => import("./pages/CreatorAnalytics"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Home = lazy(() => import("./pages/Home"));
const Login = lazy(() => import("./pages/Login"));
const Pricing = lazy(() => import("./pages/Pricing"));
const Profile = lazy(() => import("./pages/Profile"));
const ReferralPage = lazy(() => import("./pages/ReferralPage"));
const Register = lazy(() => import("./pages/Register"));
const Scheduler = lazy(() => import("./pages/Scheduler"));
const TeamSettings = lazy(() => import("./pages/TeamSettings"));
const VideoDetail = lazy(() => import("./pages/VideoDetail"));

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

function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="main-content">
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route
              path="/referral"
              element={
                <ProtectedRoute>
                  <ReferralPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/scheduler"
              element={
                <ProtectedRoute>
                  <Scheduler />
                </ProtectedRoute>
              }
            />
            <Route
              path="/team"
              element={
                <ProtectedRoute>
                  <TeamSettings />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <CreatorAnalytics />
                </ProtectedRoute>
              }
            />
            <Route
              path="/video/:videoId"
              element={
                <ProtectedRoute>
                  <VideoDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/clip-editor/:clipId"
              element={
                <ProtectedRoute>
                  <ClipEditor />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminLayout />
                </AdminRoute>
              }
            >
              <Route index element={<AdminDashboard />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="pipeline" element={<AdminPipeline />} />
              <Route path="analytics" element={<AdminAnalytics />} />
              <Route path="settings" element={<AdminSettings />} />
              <Route path="tools" element={<AdminTools />} />
            </Route>
          </Routes>
        </Suspense>
      </main>
      <FeedbackWidget />
      <Footer />
    </div>
  );
}

export default App;
