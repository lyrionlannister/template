export interface Plan {
  publicId: string;
  nombre: string;
  precioMensualCop: string;
  limiteFilasImportacion: number;
  mensajesMarketingIncluidos: number;
  precioMarketingMensajeCop: string;
  precioUtilityMensajeCop: string;
  maxUsuarios: number;
  maxWhatsappNumeros: number;
  creadoEn: string;
}

export interface PlanRequest {
  nombre: string;
  precioMensualCop: string;
  limiteFilasImportacion: number;
  mensajesMarketingIncluidos: number;
  precioMarketingMensajeCop: string;
  precioUtilityMensajeCop: string;
  maxUsuarios: number;
  maxWhatsappNumeros: number;
}
