import type { JsonTokenType } from "../utils/format-json-tokens";

export const JSON_TOKEN_CLASSES: Partial<Record<JsonTokenType, string>> = {
  key: "text-[#9C94F0]",
  string: "text-[#6FE3C3]",
  number: "text-[#F2B25C]",
};
