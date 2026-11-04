import next from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

/** Imports the design system may not make: routing and app code are injected as props. */
const OUT_OF_UI = [
  { group: ["next", "next/*"], message: "ui must not import next/*. Inject Link or the router as a prop." },
  { group: ["@/features/**", "@/lib/**", "@/stores/**", "@/components/**", "@/app/**"], message: "ui must not import app code. Pass it in as props." },
];

/** Imports pure logic may not make: no React, no Next, nothing outside kit. */
const OUT_OF_KIT = [
  { group: ["react", "react-dom", "next", "next/*"], message: "kit is pure TypeScript. Move React code to ui or the feature." },
  { group: ["@/*", "!@/kit/**"], message: "kit imports only from kit." },
];

/** Imports that reach into a feature from shared code. */
const INTO_FEATURES = [
  { group: ["@/features/**"], message: "Shared code must not import a feature. Move the shared piece to ui, kit or lib." },
];

const config = [
  { ignores: [".next/**", "node_modules/**", "public/**", "next-env.d.ts"] },
  ...next,
  ...nextTypescript,
  { files: ["src/ui/**"], rules: { "no-restricted-imports": ["error", { patterns: OUT_OF_UI }] } },
  { files: ["src/kit/**"], rules: { "no-restricted-imports": ["error", { patterns: OUT_OF_KIT }] } },
  { files: ["src/lib/**", "src/components/**"], rules: { "no-restricted-imports": ["error", { patterns: INTO_FEATURES }] } },
];

export default config;
