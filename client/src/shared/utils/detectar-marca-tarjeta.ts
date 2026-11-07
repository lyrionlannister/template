// Detección en vivo mientras se escribe el número, antes de tokenizar con Wompi.
// La marca real y confirmada viene siempre de la respuesta de tokenización.
export const detectarMarcaTarjeta = (numero: string): "Visa" | "Mastercard" | null => {
  const digitos = numero.replace(/\D/g, "");
  if (/^4/.test(digitos)) return "Visa";
  if (/^(5[1-5]|2[2-7])/.test(digitos)) return "Mastercard";
  return null;
};
