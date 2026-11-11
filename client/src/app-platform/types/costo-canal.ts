export type CanalMensajeria = "whatsapp" | "sms" | "rcs";
export type CategoriaMensaje = "marketing" | "utility" | "authentication" | "service";

export interface CostoCanal {
  publicId: string;
  canal: CanalMensajeria;
  categoria: CategoriaMensaje | null;
  proveedor: string;
  costoUnitario: string;
  moneda: string;
  vigenteDesde: string;
  vigenteHasta: string | null;
  fuente: string;
  creadoEn: string;
}
