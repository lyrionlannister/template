import type { FC } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { ProtectedRoute } from "./auth/components/protected-route";
import { AjustesPage } from "./auth/pages/ajustes-page";
import { SignInPage } from "./auth/pages/sign-in-page";
import { SignUpPage } from "./auth/pages/sign-up-page";
import { OnboardingPage } from "./billing/pages/onboarding-page";

export const App: FC = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/login" element={<SignInPage />} />
      <Route path="/registro" element={<SignUpPage />} />
      <Route
        path="/ajustes"
        element={
          <ProtectedRoute>
            <AjustesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <OnboardingPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/ajustes" replace />} />
    </Routes>
  </BrowserRouter>
);
