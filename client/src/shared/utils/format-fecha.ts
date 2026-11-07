// Las fechas (sin hora) viajan como "YYYY-MM-DD". `new Date("YYYY-MM-DD")` las
// interpreta en UTC medianoche: en un huso horario detrás de UTC, mostrarla
// con Date().toLocaleDateString() adelanta un día. Se formatea el string
// directo, sin pasar por Date().
export const formatFecha = (valor: string): string => {
  const [anio, mes, dia] = valor.split("-");
  return `${dia}/${mes}/${anio}`;
};
