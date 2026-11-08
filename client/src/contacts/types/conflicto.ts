export interface ConflictoVariable {
  publicId: string;
  clave: string;
  valorAnterior: string;
  valorNuevo: string;
  revertidoEn: string | null;
  creadoEn: string;
}
