// La tokenización de tarjeta ocurre aquí, en el navegador, directo contra
// Wompi -- nunca pasa por el backend de Pulso (ver `/CLAUDE.md` "Billing:
// solo Wompi" y Boundaries de la fase). La llave pública no es secreta: está
// diseñada para usarse del lado del cliente.
export const WOMPI_BASE_URL = import.meta.env.VITE_WOMPI_BASE_URL as string;
export const WOMPI_PUBLIC_KEY = import.meta.env.VITE_WOMPI_PUBLIC_KEY as string;
