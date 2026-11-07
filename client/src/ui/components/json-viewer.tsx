import type { FC } from "react";
import type { JsonViewerProps } from "../props/json-viewer-props";
import { formatJsonTokens } from "../utils/format-json-tokens";
import { JSON_TOKEN_CLASSES } from "../const/json-token-classes";

export const JsonViewer: FC<JsonViewerProps> = ({ value }) => (
  <pre className="bg-[#1D1B2E] text-[#D9D5F5] rounded-xl px-4.5 py-4 font-mono text-[12.5px] leading-[1.7] overflow-x-auto whitespace-pre">
    <code>
      {formatJsonTokens(value).map((token, index) => (
        <span key={index} className={JSON_TOKEN_CLASSES[token.type]}>
          {token.text}
        </span>
      ))}
    </code>
  </pre>
);
