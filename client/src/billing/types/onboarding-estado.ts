// precioCop viaja como string desde la API (nunca float). Los tokens de
// aceptación se piden aquí, no directo a Wompi desde el navegador: Wompi no
// habilita CORS en GET /merchants/info (comprobado en vivo contra el
// sandbox), a diferencia de POST /tokens/cards, que sí es para el cliente.
export interface OnboardingEstado {
  pagado: boolean;
  precioCop: string;
  acceptanceToken: string;
  acceptPersonalAuth: string;
  permalinkAceptacion: string;
  permalinkDatos: string;
}
