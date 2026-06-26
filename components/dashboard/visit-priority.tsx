import { ListChecks } from "lucide-react"
import { priorityPatients, riskMeta } from "@/lib/dashboard-data"
import { cn } from "@/lib/utils"

export function VisitPriority() {
  return (
    <section className="flex flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between border-b border-border p-5">
        <div className="flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <ListChecks className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">방문 우선순위 순위</h2>
            <p className="text-xs text-muted-foreground">AI 추천 가정방문 우선 대상자</p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="px-5 py-3 font-medium">순위</th>
              <th className="px-5 py-3 font-medium">환자명</th>
              <th className="px-5 py-3 font-medium">위험 점수</th>
              <th className="px-5 py-3 font-medium">우선순위</th>
              <th className="px-5 py-3 text-right font-medium">최근 동기화</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {priorityPatients.map((p, i) => {
              const meta = riskMeta[p.risk]
              return (
                <tr key={p.id} className="transition-colors hover:bg-muted/50">
                  <td className="px-5 py-3.5">
                    <span className="flex size-6 items-center justify-center rounded-md bg-muted text-xs font-semibold tabular-nums text-foreground">
                      {i + 1}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="font-medium text-foreground">{p.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {p.age}세 · {p.region}
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
                        <div
                          className={cn("h-full rounded-full", meta.dot)}
                          style={{ width: `${p.score}%` }}
                        />
                      </div>
                      <span className="tabular-nums font-medium text-foreground">{p.score}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
                        meta.badge,
                      )}
                    >
                      <span className={cn("size-1.5 rounded-full", meta.dot)} />
                      {meta.label}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-right text-xs text-muted-foreground">{p.lastSync}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
