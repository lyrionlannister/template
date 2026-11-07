export type JsonTokenType = "key" | "string" | "number" | "boolean" | "null" | "punct";

export interface JsonToken {
  text: string;
  type: JsonTokenType;
}

const TOKEN_REGEX =
  /("(?:\\u[0-9a-fA-F]{4}|\\[^u]|[^\\"])*"(\s*:)?|\btrue\b|\bfalse\b|\bnull\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g;

export const formatJsonTokens = (value: unknown): JsonToken[] => {
  const json = JSON.stringify(value, null, 2) ?? "";
  const tokens: JsonToken[] = [];
  let lastIndex = 0;

  for (const match of json.matchAll(TOKEN_REGEX)) {
    const text = match[0];
    const index = match.index ?? 0;
    if (index > lastIndex) tokens.push({ text: json.slice(lastIndex, index), type: "punct" });

    let type: JsonTokenType = "number";
    if (text.startsWith('"')) type = text.trimEnd().endsWith(":") ? "key" : "string";
    else if (text === "true" || text === "false") type = "boolean";
    else if (text === "null") type = "null";

    tokens.push({ text, type });
    lastIndex = index + text.length;
  }
  if (lastIndex < json.length) tokens.push({ text: json.slice(lastIndex), type: "punct" });

  return tokens;
};
