import { type FC } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "../../ui/components/button";
import { Input } from "../../ui/components/input";
import { Select } from "../../ui/components/select";
import { OPERADOR_LABEL, OPERADORES_SIN_VALOR, etiquetaDeCampo } from "../const/operadores";
import type { CampoFiltro, Condicion } from "../types/filtro";

interface ConstructorFiltroProps {
  campos: CampoFiltro[];
  condiciones: Condicion[];
  onChange: (condiciones: Condicion[]) => void;
}

export const ConstructorFiltro: FC<ConstructorFiltroProps> = ({ campos, condiciones, onChange }) => {
  const operadoresDe = (field: string) => campos.find((c) => c.field === field)?.operadores ?? [];

  const agregar = () => {
    const primerCampo = campos[0];
    if (!primerCampo) return;
    onChange([...condiciones, { field: primerCampo.field, op: primerCampo.operadores[0], value: "" }]);
  };

  const quitar = (indice: number) => onChange(condiciones.filter((_, i) => i !== indice));

  const actualizar = (indice: number, cambios: Partial<Condicion>) =>
    onChange(condiciones.map((condicion, i) => (i === indice ? { ...condicion, ...cambios } : condicion)));

  const cambiarCampo = (indice: number, field: string) => {
    const operadores = operadoresDe(field);
    actualizar(indice, { field, op: operadores[0], value: "" });
  };

  return (
    <div>
      <p className="text-ink-2 text-xs mb-3.5">
        El contacto debe cumplir <b>todas</b> las condiciones (Y).
      </p>
      <div className="flex flex-col gap-2.5">
        {condiciones.map((condicion, indice) => {
          const sinValor = OPERADORES_SIN_VALOR.includes(condicion.op);
          return (
            <div key={indice} className="flex gap-2 items-start flex-wrap sm:flex-nowrap">
              <Select
                aria-label="Variable"
                className="flex-1 min-w-35"
                value={condicion.field}
                onChange={(event) => cambiarCampo(indice, event.target.value)}
                options={campos.map((campo) => ({ value: campo.field, label: etiquetaDeCampo(campo.field) }))}
              />
              <Select
                aria-label="Operador"
                className="sm:flex-none sm:w-42.5"
                value={condicion.op}
                onChange={(event) => actualizar(indice, { op: event.target.value as Condicion["op"], value: "" })}
                options={operadoresDe(condicion.field).map((op) => ({ value: op, label: OPERADOR_LABEL[op] }))}
              />
              {!sinValor && (
                <Input
                  aria-label="Valor"
                  className="flex-1 min-w-30"
                  value={condicion.value ?? ""}
                  onChange={(event) => actualizar(indice, { value: event.target.value })}
                />
              )}
              <button
                type="button"
                onClick={() => quitar(indice)}
                aria-label="Quitar condición"
                className="flex-none w-11.5 h-11.5 grid place-items-center rounded-[13px] border border-border text-ink-3 hover:text-err-ink hover:border-err transition-colors duration-fast ease-out"
              >
                <X className="size-4" aria-hidden />
              </button>
            </div>
          );
        })}
      </div>
      <Button type="button" variant="ghost" size="sm" className="mt-2.5" onClick={agregar} disabled={campos.length === 0}>
        <Plus className="size-4" aria-hidden />
        Añadir condición
      </Button>
    </div>
  );
};
