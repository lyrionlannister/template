import type { CanalMensajeria, CategoriaMensaje } from "../types/plantilla";

export const CANAL_LABEL: Record<CanalMensajeria, string> = {
  whatsapp: "WhatsApp",
  sms: "SMS",
  rcs: "RCS",
};

export const CATEGORIA_LABEL: Record<CategoriaMensaje, string> = {
  marketing: "Marketing",
  utility: "Utilidad",
  authentication: "Autenticación",
  service: "Servicio",
};

export const CANALES: CanalMensajeria[] = ["whatsapp", "sms", "rcs"];
