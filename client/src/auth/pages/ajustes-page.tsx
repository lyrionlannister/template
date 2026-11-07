import { useEffect, useState, type FC, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { LogOut, Settings, UserPlus } from "lucide-react";
import { useAuth } from "../hooks/use-auth";
import type { Plan } from "../types/plan";
import type { Usuario } from "../types/usuario";
import { ApiError } from "../../shared/types/api-error";
import { formatCop } from "../../shared/utils/format-cop";
import { Alert } from "../../ui/components/alert";
import { AppShell } from "../../ui/components/app-shell";
import { Button } from "../../ui/components/button";
import { Field } from "../../ui/components/field";
import { Input } from "../../ui/components/input";
import { PersonRow } from "../../ui/components/person-row";
import { Pill } from "../../ui/components/pill";
import { Spinner } from "../../ui/components/spinner";
import { Tabs } from "../../ui/components/tabs";

const NAV_ITEMS = [{ label: "Ajustes", href: "/ajustes", icon: Settings }];

const inicialesDe = (email: string): string => email.slice(0, 2).toUpperCase();

export const AjustesPage: FC = () => {
  const { obtenerSesionActual, obtenerMiPlan, invitarUsuario, cerrarSesion } = useAuth();
  const navigate = useNavigate();

  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [tab, setTab] = useState("equipo");

  const [inviteEmail, setInviteEmail] = useState("");
  const [invitePassword, setInvitePassword] = useState("");
  const [invitando, setInvitando] = useState(false);
  const [errorInvite, setErrorInvite] = useState<string | null>(null);
  const [exitoInvite, setExitoInvite] = useState(false);

  useEffect(() => {
    Promise.all([obtenerSesionActual(), obtenerMiPlan()])
      .then(([sesion, miPlan]) => {
        setUsuario(sesion);
        setPlan(miPlan);
      })
      .catch((err) => setErrorCarga(err instanceof ApiError ? err.message : "No se pudo cargar Ajustes."))
      .finally(() => setCargando(false));
  }, [obtenerSesionActual, obtenerMiPlan]);

  const invitar = async (event: FormEvent) => {
    event.preventDefault();
    setInvitando(true);
    setErrorInvite(null);
    setExitoInvite(false);
    try {
      await invitarUsuario({ email: inviteEmail, password: invitePassword });
      setInviteEmail("");
      setInvitePassword("");
      setExitoInvite(true);
    } catch (err) {
      setErrorInvite(err instanceof ApiError ? err.message : "No se pudo invitar a este correo.");
    } finally {
      setInvitando(false);
    }
  };

  const salir = async () => {
    await cerrarSesion();
    navigate("/login");
  };

  return (
    <AppShell
      navItems={NAV_ITEMS}
      activeHref="/ajustes"
      logoLabel="Pulso"
      userName={usuario?.email ?? ""}
      userInitials={usuario ? inicialesDe(usuario.email) : "--"}
    >
      <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
        <div>
          <h1 className="text-[22px] mb-1">Ajustes</h1>
          <p className="text-ink-2 text-sm">Equipo y plan de tu negocio.</p>
        </div>
        <Button variant="ghost" size="sm" onClick={salir}>
          <LogOut className="size-4" aria-hidden />
          Cerrar sesión
        </Button>
      </div>

      {cargando ? (
        <div className="grid place-items-center py-16">
          <Spinner />
        </div>
      ) : errorCarga ? (
        <Alert variant="err" title="No se pudo cargar Ajustes">
          {errorCarga}
        </Alert>
      ) : (
        <>
          <Tabs
            options={[
              { value: "equipo", label: "Equipo" },
              { value: "plan", label: "Plan" },
            ]}
            value={tab}
            onChange={setTab}
          />

          <div className="mt-5">
            {tab === "equipo" && usuario && (
              <div className="bg-surface border border-border rounded-md p-4.75 max-w-xl">
                <PersonRow
                  name={usuario.email}
                  subtitle={usuario.rol === "administrador" ? "Tú · Administrador" : "Tú · Miembro"}
                  initials={inicialesDe(usuario.email)}
                />
                <div className="mt-2">
                  <Pill variant={usuario.rol === "administrador" ? "brand" : "neutral"}>
                    {usuario.rol === "administrador" ? "Administrador" : "Miembro"}
                  </Pill>
                </div>

                <div className="h-px bg-border my-5" />

                {usuario.rol === "administrador" ? (
                  <>
                    <h3 className="text-[15px] font-semibold mb-3.5 flex items-center gap-2">
                      <UserPlus className="size-4.5 text-brand" aria-hidden />
                      Invitar a alguien de tu equipo
                    </h3>
                    <form onSubmit={invitar}>
                      <Field label="Correo" htmlFor="invite-email">
                        <Input
                          id="invite-email"
                          type="email"
                          value={inviteEmail}
                          onChange={(event) => setInviteEmail(event.target.value)}
                          required
                        />
                      </Field>
                      <Field
                        label="Contraseña temporal"
                        htmlFor="invite-password"
                        hint="Compártela con la persona para que inicie sesión."
                      >
                        <Input
                          id="invite-password"
                          type="password"
                          value={invitePassword}
                          onChange={(event) => setInvitePassword(event.target.value)}
                          required
                        />
                      </Field>
                      {errorInvite && (
                        <div className="mb-4.5">
                          <Alert variant="err" title="No se pudo invitar">
                            {errorInvite}
                          </Alert>
                        </div>
                      )}
                      {exitoInvite && (
                        <div className="mb-4.5">
                          <Alert variant="ok" title="Invitación creada">
                            Ya puede iniciar sesión con ese correo y esa contraseña.
                          </Alert>
                        </div>
                      )}
                      <Button type="submit" loading={invitando} className="w-full justify-center">
                        Invitar
                      </Button>
                    </form>
                  </>
                ) : (
                  <p className="text-ink-2 text-sm">Solo un administrador puede invitar a más personas.</p>
                )}
              </div>
            )}

            {tab === "plan" && plan && (
              <div className="bg-surface border border-border rounded-md p-4.75 max-w-xl">
                <h3 className="text-[16px] font-semibold mb-1">Plan {plan.nombre}</h3>
                <p className="text-ink-2 text-sm mb-4.5">{formatCop(plan.precioMensualCop)} / mes</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-4">
                  <div>
                    <span className="text-xs text-ink-3">Mensajes de marketing incluidos</span>
                    <div className="font-semibold">{plan.mensajesMarketingIncluidos.toLocaleString("es-CO")}</div>
                  </div>
                  <div>
                    <span className="text-xs text-ink-3">Límite de importación</span>
                    <div className="font-semibold">{plan.limiteFilasImportacion.toLocaleString("es-CO")} filas</div>
                  </div>
                  <div>
                    <span className="text-xs text-ink-3">Usuarios incluidos</span>
                    <div className="font-semibold">{plan.maxUsuarios}</div>
                  </div>
                  <div>
                    <span className="text-xs text-ink-3">Números de WhatsApp incluidos</span>
                    <div className="font-semibold">{plan.maxWhatsappNumeros}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </AppShell>
  );
};
