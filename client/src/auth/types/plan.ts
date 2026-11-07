// Los montos en COP viajan como string desde la API (nunca float), ver
// skill money-precision -- se formatean en el componente que los muestra.
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
