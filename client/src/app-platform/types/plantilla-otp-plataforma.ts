export type EstadoPlantillaMeta = "PENDING" | "APPROVED" | "REJECTED";

export interface PlantillaOtpPlataforma {
  publicId: string;
  nombre: string;
  idioma: string;
  estadoMeta: EstadoPlantillaMeta;
  creadoEn: string;
}
