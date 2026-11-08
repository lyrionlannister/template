export interface Contacto {
  publicId: string;
  telefono: string;
  variables: Record<string, string>;
  creadoEn: string;
}

export interface ContactosPaginados {
  contactos: Contacto[];
  total: number;
  pagina: number;
  porPagina: number;
}
