import { useCallback, useEffect, useState } from "react";

type Tema = "light" | "dark";

const CLAVE = "pulso-tema";

const leerTemaGuardado = (): Tema | null => {
  try {
    const valor = localStorage.getItem(CLAVE);
    return valor === "light" || valor === "dark" ? valor : null;
  } catch {
    return null;
  }
};

const prefiereOscuro = (): boolean =>
  typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;

export const useTheme = () => {
  const [tema, setTema] = useState<Tema>(() => leerTemaGuardado() ?? (prefiereOscuro() ? "dark" : "light"));

  useEffect(() => {
    document.documentElement.dataset.theme = tema;
    try {
      localStorage.setItem(CLAVE, tema);
    } catch {
      // Navegación privada o storage bloqueado: el tema igual aplica, solo no persiste.
    }
  }, [tema]);

  const alternar = useCallback(() => setTema((actual) => (actual === "dark" ? "light" : "dark")), []);

  return { tema, alternar };
};
