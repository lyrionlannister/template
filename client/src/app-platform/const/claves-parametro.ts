// Identificadores de parámetro conocidos (no son precios ni valores comerciales,
// solo el nombre de la clave) -- ver "Planes iniciales y mensajes incluidos" en /CLAUDE.md.
export const CLAVES_PARAMETRO_CONOCIDAS = [
  "trial_dias",
  "trial_mensajes_gratis",
  "onboarding_precio_cop",
  "comision_wompi_porcentaje",
  "comision_wompi_fijo_cop",
  "comision_wompi_iva_porcentaje",
  "impago_reintentos_max",
  "impago_dias_entre_reintentos",
  "sms_rcs_margen_porcentaje",
  "sms_rcs_mensajes_por_contacto_mes",
  "precio_venta_sms_cop",
  "precio_venta_rcs_cop",
] as const;
