export type MedioRecarga = "tarjeta" | "pse" | "nequi";
export type EstadoMovimiento = "pendiente" | "aprobada" | "rechazada" | "error";

// montoCop viaja como string desde la API (nunca float).
export interface MovimientoSaldo {
  publicId: string;
  estado: EstadoMovimiento;
  medio: MedioRecarga | null;
  montoCop: string;
  referencia: string;
}

export interface SaldoEstado {
  saldoCop: string;
  movimientos: MovimientoSaldo[];
}

export interface InstitucionFinanciera {
  code: string;
  name: string;
}

export interface RecargaPseResultado {
  movimiento: MovimientoSaldo;
  asyncPaymentUrl: string | null;
}
