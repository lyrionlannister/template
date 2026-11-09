import type { FiltroAudiencia } from "./filtro";

export type TipoAudiencia = "dinamica" | "estatica";

export interface Audiencia {
  publicId: string;
  nombre: string;
  tipo: TipoAudiencia;
  filtro: FiltroAudiencia;
  conteo: number;
  congeladaEn: string | null;
  creadoEn: string;
}

export interface AudienciasPaginadas {
  audiencias: Audiencia[];
  total: number;
  pagina: number;
  porPagina: number;
}
