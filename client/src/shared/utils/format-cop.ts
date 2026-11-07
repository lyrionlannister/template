// Los montos en COP llegan como string desde la API (nunca float, ver skill
// money-precision). `Number()` aquí es solo para presentación, no para calcular.
export const formatCop = (valor: string): string =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(valor));
