import { createRoot } from "react-dom/client";

export function mountScaffold(container: HTMLElement): () => void {
  const root = createRoot(container);
  root.render(<p>BenefitBridge synthetic workspace fixture</p>);
  return () => root.unmount();
}
