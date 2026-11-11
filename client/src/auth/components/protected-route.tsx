import { useEffect, useState, type FC } from "react";
import { Navigate } from "react-router";
import { useAuth } from "../hooks/use-auth";
import type { ProtectedRouteProps } from "../props/protected-route-props";
import { Spinner } from "../../ui/components/spinner";

type Estado = "cargando" | "autenticado" | "no-autenticado" | "no-autorizado";

export const ProtectedRoute: FC<ProtectedRouteProps> = ({ children, soloSuperadmin = false }) => {
  const { obtenerSesionActual } = useAuth();
  const [estado, setEstado] = useState<Estado>("cargando");

  useEffect(() => {
    let vigente = true;
    obtenerSesionActual()
      .then((usuario) => {
        if (!vigente) return;
        setEstado(soloSuperadmin && !usuario.esSuperadmin ? "no-autorizado" : "autenticado");
      })
      .catch(() => vigente && setEstado("no-autenticado"));
    return () => {
      vigente = false;
    };
  }, [obtenerSesionActual, soloSuperadmin]);

  if (estado === "cargando") {
    return (
      <div className="h-screen grid place-items-center bg-bg">
        <Spinner size="lg" />
      </div>
    );
  }

  if (estado === "no-autenticado") {
    return <Navigate to="/login" replace />;
  }

  if (estado === "no-autorizado") {
    return <Navigate to="/ajustes" replace />;
  }

  return <>{children}</>;
};
