export type Operador = "eq" | "neq" | "contains" | "gt" | "gte" | "lt" | "lte" | "exists" | "not_exists";

export interface Condicion {
  field: string;
  op: Operador;
  value?: string | number | null;
}

export interface FiltroAudiencia {
  and: Condicion[];
}

export interface CampoFiltro {
  field: string;
  operadores: Operador[];
}
