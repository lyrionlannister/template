export type RolUsuario = "administrador" | "miembro";

export interface Usuario {
  publicId: string;
  email: string;
  rol: RolUsuario;
  mfaHabilitado: boolean;
}
