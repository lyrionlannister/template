export interface TipoCambio {
  publicId: string;
  par: string;
  valor: string;
  fuente: string;
  vigenteDesde: string;
  vigenteHasta: string | null;
  creadoEn: string;
}
