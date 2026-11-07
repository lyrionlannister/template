export const extractMessage = (body: Record<string, unknown>, fallback: string): string => {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return (detail as Array<{ msg?: string }>).map((e) => e.msg ?? "").filter(Boolean).join(", ") || fallback;
  }
  return (body?.error as string) ?? fallback;
};