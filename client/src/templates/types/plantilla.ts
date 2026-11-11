export type CanalMensajeria = "whatsapp" | "sms" | "rcs";
export type CategoriaMensaje = "marketing" | "utility" | "authentication" | "service";

export interface Plantilla {
  publicId: string;
  nombre: string;
  canal: CanalMensajeria;
  contenido: string;
  variables: string[];
  categoria: CategoriaMensaje | null;
  nombrePlantillaMeta: string | null;
  nombrePlantillaSent: string | null;
  creadoEn: string;
}

export interface PlantillasPaginadas {
  plantillas: Plantilla[];
  total: number;
  pagina: number;
  porPagina: number;
}

export interface ContactoConVariableFaltante {
  contactoPublicId: string;
  telefono: string;
  variablesFaltantes: string[];
}

export interface VerificarAudienciaResultado {
  totalContactos: number;
  contactosConVariableFaltante: ContactoConVariableFaltante[];
}
