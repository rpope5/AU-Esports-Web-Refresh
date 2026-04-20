"use client";

import { useState } from "react";

type Props = {
  triggerLabel: string;
  confirmMessage: string;
  onConfirm: () => Promise<void> | void;
  confirmLabel?: string;
  pendingLabel?: string;
  busy?: boolean;
};

export default function InlineDestructiveConfirm({
  triggerLabel,
  confirmMessage,
  onConfirm,
  confirmLabel = "Delete Permanently",
  pendingLabel = "Deleting...",
  busy = false,
}: Props) {
  const [isOpen, setIsOpen] = useState(false);

  async function handleConfirm() {
    try {
      await onConfirm();
      setIsOpen(false);
    } catch {
      // Keep the confirmation open so the user can retry after seeing the page-level error message.
    }
  }

  return (
    <div className="inline-flex flex-col items-start">
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        disabled={busy}
        className="rounded-md border border-red-700 px-3 py-1 text-xs font-medium text-red-300 transition hover:bg-red-950/50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {triggerLabel}
      </button>

      {isOpen && (
        <div className="mt-3 max-w-md rounded-lg border border-red-900 bg-red-950/40 p-3">
          <p className="text-sm text-red-200">{confirmMessage}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              disabled={busy}
              className="rounded-md border border-neutral-700 px-3 py-1 text-xs text-neutral-200 transition hover:bg-neutral-900 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => void handleConfirm()}
              disabled={busy}
              className="rounded-md border border-red-700 bg-red-900/50 px-3 py-1 text-xs font-semibold text-red-100 transition hover:bg-red-900 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? pendingLabel : confirmLabel}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

