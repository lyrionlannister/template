export interface SuscripcionEstado {
  existe: boolean;
  estado: string | null;
  // montoCop viaja como string desde la API (nunca float).
  montoCop: string | null;
  proximaFechaCobro: string | null;
}
