import { useCallback } from "react";
import { WOMPI_BASE_URL, WOMPI_PUBLIC_KEY } from "../const/wompi-config";

export interface DatosTarjeta {
  numero: string;
  cvc: string;
  mesExpiracion: string;
  anioExpiracion: string;
  titular: string;
}

export interface TarjetaTokenizada {
  token: string;
  marca: string;
  ultimosCuatro: string;
  mesExpiracion: string;
  anioExpiracion: string;
  titular: string;
}

// Llama directo a Wompi desde el navegador, nunca al backend de Pulso: el
// número de tarjeta no debe tocar nuestro servidor (ver Boundaries de
// `resources/specs/SPEC-billing.md`). Los tokens de aceptación, en cambio,
// se piden al backend (ver `use-billing.ts`): Wompi no habilita CORS para
// GET /merchants/info.
export const useWompiTokenizacion = () => {
  const tokenizarTarjeta = useCallback(async (datos: DatosTarjeta): Promise<TarjetaTokenizada> => {
    const respuesta = await fetch(`${WOMPI_BASE_URL}/tokens/cards`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${WOMPI_PUBLIC_KEY}`,
      },
      body: JSON.stringify({
        number: datos.numero.replace(/\s+/g, ""),
        cvc: datos.cvc,
        exp_month: datos.mesExpiracion,
        exp_year: datos.anioExpiracion,
        card_holder: datos.titular,
      }),
    });
    const cuerpo = await respuesta.json();
    if (!respuesta.ok) {
      throw new Error("No se pudo validar la tarjeta. Revisa los datos e intenta de nuevo.");
    }
    // Wompi devuelve marca/últimos 4/vencimiento junto con el token -- se
    // guardan en Pulso solo para mostrarle la tarjeta al usuario, nunca el
    // número completo ni el CVC (eso se queda en Wompi).
    return {
      token: cuerpo.data.id as string,
      marca: cuerpo.data.brand as string,
      ultimosCuatro: cuerpo.data.last_four as string,
      mesExpiracion: cuerpo.data.exp_month as string,
      anioExpiracion: cuerpo.data.exp_year as string,
      titular: datos.titular,
    };
  }, []);

  return { tokenizarTarjeta };
};
