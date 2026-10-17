import type { ReactNode } from "react";

import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { FeedPage } from "./pages/FeedPage";
import { LoginPage } from "./pages/LoginPage";
import { PublicationPage } from "./pages/PublicationPage";
import { ProfilePage } from "./pages/ProfilePage";

function ProtectedRoute({
  children,
}: {
  children: ReactNode;
}) {
  const token =
    localStorage.getItem("access_token");

  if (!token) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  return children;
}


function App() {
  return (
    <Routes>
      <Route
  path="/profile"
  element={
    <ProtectedRoute>
      <ProfilePage />
    </ProtectedRoute>
  }
/>
      <Route
  path="/publications/:id"
  element={
    <ProtectedRoute>
      <PublicationPage />
    </ProtectedRoute>
  }
/>
      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <FeedPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}


export default App;