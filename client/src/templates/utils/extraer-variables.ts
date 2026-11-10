const PATRON_VARIABLE = /\{\{([a-zA-Z0-9_]+)\}\}/g;

export const extraerVariables = (contenido: string): string[] => {
  const vistas: string[] = [];
  for (const match of contenido.matchAll(PATRON_VARIABLE)) {
    const clave = match[1];
    if (!vistas.includes(clave)) vistas.push(clave);
  }
  return vistas;
};
