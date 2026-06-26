import { Sparkles, ChevronRight } from "lucide-react"
import { aiAlerts } from "@/lib/dashboard-data"
import { Button } from "@/components/ui/button"

export function AiAlertPanel() {
  return (
    <section className="flex flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between border-b border-border p-5">
        <div className="flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-lg bg-risk-high/10 text-risk-high">
            <Sparkles className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">AI 긴급 알림</h2>
            <p className="text-xs text-muted-foreground">즉시 조치가 필요한 신규 고위험 대상자</p>
          </div>
        </div>
        <span className="rounded-full bg-risk-high/10 px-2.5 py-1 text-xs font-semibold text-risk-high">
          {aiAlerts.length}건 신규
        </span>
      </div>

      <ul className="divide-y divide-border">
        {aiAlerts.map((alert) => (
          <li key={alert.id} className="flex items-start gap-3 p-4 transition-colors hover:bg-muted/50">
            <span className="mt-1.5 flex size-2 shrink-0 rounded-full bg-risk-high" aria-hidden />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold text-foreground">
                  {alert.name}
                  <span className="ml-1 text-xs font-normal text-muted-foreground">
                    {alert.age}세 · {alert.region}
                  </span>
                </p>
              </div>
              <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{alert.reason}</p>
              <p className="mt-1.5 text-[11px] text-muted-foreground/70">{alert.detectedAt} 감지</p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className="text-base font-semibold tabular-nums text-risk-high">{alert.score}</span>
              <span className="text-[10px] text-muted-foreground">위험점수</span>
            </div>
          </li>
        ))}
      </ul>

      <div className="p-3">
        <Button variant="ghost" className="w-full justify-center text-sm text-primary">
          전체 알림 보기
          <ChevronRight className="size-4" />
        </Button>
      </div>
    </section>
  )
}
