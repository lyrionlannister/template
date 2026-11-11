// El App ID y el config_id de Embedded Signup no son secretos: son
// públicos por diseño del SDK de Meta, pensados para usarse en el
// navegador (el secreto real, META_APP_SECRET, nunca sale del backend).
export const META_APP_ID = import.meta.env.VITE_META_APP_ID as string;
export const META_CONFIG_ID = import.meta.env.VITE_META_CONFIG_ID as string;
