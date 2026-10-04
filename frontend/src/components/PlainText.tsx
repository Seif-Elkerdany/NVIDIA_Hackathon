export function PlainText({ text, label }: { text: string; label?: string }) {
  // Provider text is untrusted data. React escapes it; Markdown/HTML is never injected.
  return (
    <div className="plain-text" aria-label={label}>
      {text}
    </div>
  );
}
