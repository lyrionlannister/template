export type EstadoFuenteDePago = "pendiente" | "disponible" | "fallida";

export interface FuenteDePago {
  publicId: string;
  estado: EstadoFuenteDePago;
}

export interface EstadoFuenteDePagoPolling {
  estado: EstadoFuenteDePago;
  pasoActual: "BROWSER_INFO" | "CHALLENGE" | null;
  iframeHtml: string | null;
}

export interface TokensDeAceptacion {
  acceptanceToken: string;
  acceptPersonalAuth: string;
  permalinkAceptacion: string;
  permalinkDatos: string;
}
