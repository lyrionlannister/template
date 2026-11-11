import type { CanalMensajeria, CategoriaMensaje } from "../types/costo-canal";
import type { EstadoPlantillaMeta } from "../types/plantilla-otp-plataforma";

export const CANAL_LABEL: Record<CanalMensajeria, string> = {
  whatsapp: "WhatsApp",
  sms: "SMS",
  rcs: "RCS",
};

export const CATEGORIA_LABEL: Record<CategoriaMensaje, string> = {
  marketing: "Marketing",
  utility: "Utility",
  authentication: "Authentication",
  service: "Service",
};

export const ESTADO_PLANTILLA_LABEL: Record<EstadoPlantillaMeta, string> = {
  PENDING: "Pendiente de aprobación",
  APPROVED: "Aprobada",
  REJECTED: "Rechazada",
};

export const ESTADO_PLANTILLA_PILL: Record<EstadoPlantillaMeta, "warn" | "ok" | "err"> = {
  PENDING: "warn",
  APPROVED: "ok",
  REJECTED: "err",
};
