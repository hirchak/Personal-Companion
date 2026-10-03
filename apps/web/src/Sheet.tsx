import { useEffect, useRef, type ReactNode } from "react";
export function Sheet({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current!;
    const prior = document.activeElement as HTMLElement | null;
    d.showModal();
    d.querySelector<HTMLElement>("[data-sheet-focus], [autofocus]")?.focus();
    return () => {
      d.close();
      prior?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={"app-sheet" + (wide ? " sheet-wide" : "")}
      aria-label={title}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <header className="sheet-heading">
        <h2>{title}</h2>
        <button onClick={onClose} aria-label={"Закрити: " + title}>
          Закрити
        </button>
      </header>
      {children}
    </dialog>
  );
}
