import type { Operador } from "../types/filtro";

export const OPERADOR_LABEL: Record<Operador, string> = {
  eq: "es igual a",
  neq: "no es igual a",
  contains: "contiene",
  gt: "mayor que",
  gte: "mayor o igual que",
  lt: "menor que",
  lte: "menor o igual que",
  exists: "existe",
  not_exists: "no existe",
};

export const OPERADORES_SIN_VALOR: Operador[] = ["exists", "not_exists"];

export const CAMPO_LABEL: Record<string, string> = {
  telefono: "Teléfono",
  creado_en: "Fecha de creación",
};

export const etiquetaDeCampo = (field: string): string => {
  if (CAMPO_LABEL[field]) return CAMPO_LABEL[field];
  if (field.startsWith("variables.")) return field.slice("variables.".length);
  return field;
};
