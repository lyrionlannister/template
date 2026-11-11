// El navegador decide el idioma del globo nativo de validación
// (`required`, `type="email"`, etc.) según el idioma del propio Chrome/OS,
// no el `lang` de la página -- por eso un usuario con Chrome en inglés ve
// "Please fill out this field" aunque toda la interfaz esté en español.
// `setCustomValidity` reemplaza ese texto por uno fijo nuestro; limpiarlo
// en cada cambio es obligatorio o el campo queda inválido para siempre.
type ElementoValidable = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;

const mensajeDeValidacionNativa = (el: ElementoValidable): string => {
  const v = el.validity;
  if (v.valueMissing) return "Completa este campo.";
  if (v.typeMismatch) return "El formato no es válido.";
  if (v.tooShort && "minLength" in el) return `Debe tener al menos ${el.minLength} caracteres.`;
  if (v.tooLong && "maxLength" in el) return `No puede superar ${el.maxLength} caracteres.`;
  if (v.patternMismatch) return "El formato no es válido.";
  if (v.rangeUnderflow || v.rangeOverflow || v.stepMismatch) return "El valor no es válido.";
  return "Revisa este campo.";
};

export const alInvalidoEnEspanol = <E extends ElementoValidable>(event: { currentTarget: E }): void => {
  event.currentTarget.setCustomValidity(mensajeDeValidacionNativa(event.currentTarget));
};

export const limpiarValidezNativa = <E extends ElementoValidable>(event: { currentTarget: E }): void => {
  event.currentTarget.setCustomValidity("");
};
