import type { FC } from "react";
import { Navigate, Route, Routes } from "react-router";
import { AudienciaDetallePage } from "./audiences/pages/audiencia-detalle-page";
import { AudienciasPage } from "./audiences/pages/audiencias-page";
import { NuevaAudienciaPage } from "./audiences/pages/nueva-audiencia-page";
import { ProtectedRoute } from "./auth/components/protected-route";
import { AjustesPage } from "./auth/pages/ajustes-page";
import { OlvidePasswordPage } from "./auth/pages/olvide-password-page";
import { RestablecerPasswordPage } from "./auth/pages/restablecer-password-page";
import { SignInPage } from "./auth/pages/sign-in-page";
import { SignUpPage } from "./auth/pages/sign-up-page";
import { OnboardingPage } from "./billing/pages/onboarding-page";
import { SaldoPage } from "./billing/pages/saldo-page";
import { SuscripcionPage } from "./billing/pages/suscripcion-page";
import { ConfiguracionContactosPage } from "./contacts/pages/configuracion-contactos-page";
import { ContactosPage } from "./contacts/pages/contactos-page";
import { ImportarContactosPage } from "./contacts/pages/importar-contactos-page";
import { NuevaPlantillaPage } from "./templates/pages/nueva-plantilla-page";
import { PlantillaDetallePage } from "./templates/pages/plantilla-detalle-page";
import { PlantillasPage } from "./templates/pages/plantillas-page";

export const AppRoutes: FC = () => (
  <Routes>
    <Route path="/login" element={<SignInPage />} />
    <Route path="/registro" element={<SignUpPage />} />
    <Route path="/olvide-password" element={<OlvidePasswordPage />} />
    <Route path="/restablecer-password" element={<RestablecerPasswordPage />} />
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
    <Route
      path="/suscripcion"
      element={
        <ProtectedRoute>
          <SuscripcionPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/saldo"
      element={
        <ProtectedRoute>
          <SaldoPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/contactos"
      element={
        <ProtectedRoute>
          <ContactosPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/contactos/importar"
      element={
        <ProtectedRoute>
          <ImportarContactosPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/contactos/configuracion"
      element={
        <ProtectedRoute>
          <ConfiguracionContactosPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/audiencias"
      element={
        <ProtectedRoute>
          <AudienciasPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/audiencias/nueva"
      element={
        <ProtectedRoute>
          <NuevaAudienciaPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/audiencias/:publicId"
      element={
        <ProtectedRoute>
          <AudienciaDetallePage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/plantillas"
      element={
        <ProtectedRoute>
          <PlantillasPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/plantillas/nueva"
      element={
        <ProtectedRoute>
          <NuevaPlantillaPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/plantillas/:publicId"
      element={
        <ProtectedRoute>
          <PlantillaDetallePage />
        </ProtectedRoute>
      }
    />
    <Route path="*" element={<Navigate to="/ajustes" replace />} />
  </Routes>
);
