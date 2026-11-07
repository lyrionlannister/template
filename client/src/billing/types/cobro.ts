export type EstadoCobro = "pendiente" | "aprobada" | "rechazada" | "error";

// montoCop viaja como string desde la API (nunca float, ver skill money-precision).
export interface Cobro {
  estado: EstadoCobro;
  montoCop: string;
  referencia: string;
}
