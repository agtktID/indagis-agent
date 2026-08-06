import { Typography } from "@nous-research/ui/ui/components/typography/index";
import type { StatusResponse } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useI18n } from "@/i18n";

export function SidebarFooter({ status }: SidebarFooterProps) {
  const { t } = useI18n();

  return (
    <div
      className={cn(
        "flex shrink-0 flex-col gap-1",
        "px-5 py-2.5",
        "border-t border-current/10",
      )}
    >
      <div className="flex shrink-0 items-center justify-between gap-2">
        <Typography
          className="font-mono-ui text-xs tabular-nums tracking-[0.08em] text-text-tertiary lowercase"
        >
          {status?.version != null ? `v${status.version}` : "—"}
        </Typography>

        <a
          href="https://nousresearch.com"
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            "font-sans text-display text-xs tracking-[0.12em] text-midground",
            "transition-opacity hover:opacity-90",
            "focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-midground/40",
          )}
        >
          {t.app.footer.org}
        </a>
      </div>

      {/* Indagis → Hermes attribution. Mandated by the upstream MIT license
          and the design-system spec: a single, always-visible "Built on"
          line below the version footer. Links to the original NousResearch
          repository so the credit is verifiable. */}
      <a
        href="https://github.com/NousResearch/hermes-agent"
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "font-mono-ui text-[10px] tabular-nums tracking-[0.06em]",
          "text-text-tertiary/70 transition-colors hover:text-text-secondary",
          "focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-midground/40",
        )}
      >
        Built on Hermes Agent · NousResearch · MIT License
      </a>
    </div>
  );
}

interface SidebarFooterProps {
  status: StatusResponse | null;
}
