export interface ParametroComercial {
  publicId: string;
  clave: string;
  valor: string;
  fuente: string;
  vigenteDesde: string;
  vigenteHasta: string | null;
  creadoEn: string;
}
