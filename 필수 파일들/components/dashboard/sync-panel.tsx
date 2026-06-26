import { RefreshCw, Database, CheckCircle2, Loader2, Clock } from "lucide-react"
import { syncRecords, type SyncRecord } from "@/lib/dashboard-data"
import { cn } from "@/lib/utils"

const statusMeta: Record<
  SyncRecord["status"],
  { icon: typeof CheckCircle2; class: string }
> = {
  완료: { icon: CheckCircle2, class: "text-risk-low" },
  "동기화 중": { icon: Loader2, class: "text-primary animate-spin" },
  지연: { icon: Clock, class: "text-risk-medium" },
}

export function SyncPanel() {
  return (
    <section className="flex flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between border-b border-border p-5">
        <div className="flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <RefreshCw className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">최근 데이터 동기화</h2>
            <p className="text-xs text-muted-foreground">외부 연동 데이터 수집 현황</p>
          </div>
        </div>
        <span className="hidden text-xs text-muted-foreground sm:block">최종 갱신 09:02</span>
      </div>

      <ul className="divide-y divide-border">
        {syncRecords.map((rec) => {
          const meta = statusMeta[rec.status]
          const Icon = meta.icon
          return (
            <li key={rec.source} className="flex items-center gap-3 p-4 transition-colors hover:bg-muted/50">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <Database className="size-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{rec.source}</p>
                <p className="truncate text-xs text-muted-foreground">{rec.description}</p>
              </div>
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium tabular-nums text-foreground">
                  {rec.records.toLocaleString()}건
                </p>
                <p className="text-[11px] text-muted-foreground">{rec.time}</p>
              </div>
              <span className="flex items-center gap-1.5">
                <Icon className={cn("size-4", meta.class)} />
                <span className="text-xs font-medium text-foreground">{rec.status}</span>
              </span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
