export type EstadoImportacion = "pendiente" | "procesando" | "completada" | "fallida";

export interface PrevisualizacionImportacion {
  previewId: string;
  columnas: string[];
  muestra: Record<string, string>[];
  totalFilas: number;
}

export interface ImportacionContacto {
  publicId: string;
  estado: EstadoImportacion;
  totalFilas: number;
}

export interface EstadoImportacionDetalle extends ImportacionContacto {
  filasAceptadas: number;
  filasRechazadas: number;
  filasConAdvertencia: number;
  motivoFallo: string | null;
}

export interface ContactoRechazado {
  filaCruda: Record<string, string>;
  motivo: string;
}

export interface RechazosPaginados {
  rechazos: ContactoRechazado[];
  total: number;
  pagina: number;
  porPagina: number;
}
