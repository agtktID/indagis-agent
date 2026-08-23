import { Typography } from "@nous-research/ui/ui/components/typography/index";
import type { StatusResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

export function SidebarFooter({ status }: SidebarFooterProps) {
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
      </div>
    </div>
  );
}

interface SidebarFooterProps {
  status: StatusResponse | null;
}
