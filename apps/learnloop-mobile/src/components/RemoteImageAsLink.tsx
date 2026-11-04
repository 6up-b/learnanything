import type { ComponentProps } from "react";
import type ReactMarkdown from "react-markdown";

type Components = NonNullable<ComponentProps<typeof ReactMarkdown>["components"]>;

/** §3.4: the host's CSP has no remote images, so one renders as the link it is. */
export const RemoteImageAsLink: Components = {
  img: ({ src, alt }) => <a href={src} rel="noreferrer noopener" target="_blank">{alt || "image"}</a>
};
