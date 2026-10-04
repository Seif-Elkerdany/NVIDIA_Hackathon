import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { build } from "vite";

test("React renders escaped synthetic content", () => {
  assert.equal(
    renderToStaticMarkup(createElement("p", null, "<synthetic>")),
    "<p>&lt;synthetic&gt;</p>",
  );
});

test("Vite bundles the strict TypeScript React fixture without a web shell", async () => {
  const result = await build({
    configFile: false,
    logLevel: "silent",
    build: {
      write: false,
      lib: {
        entry: fileURLToPath(new URL("./scaffold.tsx", import.meta.url)),
        formats: ["es"],
      },
      rollupOptions: {
        external: ["react", "react/jsx-runtime", "react-dom/client"],
      },
    },
    esbuild: { jsx: "automatic" },
  });
  const bundles = Array.isArray(result) ? result : [result];
  assert.ok(
    bundles.some((bundle) =>
      bundle.output.some(
        (item) =>
          item.type === "chunk" && item.exports.includes("mountScaffold"),
      ),
    ),
  );
});
