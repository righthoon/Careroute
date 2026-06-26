import { Users, AlertTriangle, AlertCircle, ShieldCheck, TrendingUp, TrendingDown } from "lucide-react"
import { summaryStats } from "@/lib/dashboard-data"
import { cn } from "@/lib/utils"

const cards = [
  {
    label: "총 관리 대상자",
    value: summaryStats.total,
    icon: Users,
    iconClass: "bg-primary/10 text-primary",
    trend: "+3.2%",
    up: true,
    note: "지난주 대비",
  },
  {
    label: "고위험 환자",
    value: summaryStats.high,
    icon: AlertTriangle,
    iconClass: "bg-risk-high/10 text-risk-high",
    trend: "+8명",
    up: true,
    note: "신규 식별",
    accent: "text-risk-high",
  },
  {
    label: "중위험 환자",
    value: summaryStats.medium,
    icon: AlertCircle,
    iconClass: "bg-risk-medium/15 text-risk-medium",
    trend: "-2.1%",
    up: false,
    note: "지난주 대비",
  },
  {
    label: "저위험 환자",
    value: summaryStats.low,
    icon: ShieldCheck,
    iconClass: "bg-risk-low/10 text-risk-low",
    trend: "+1.4%",
    up: true,
    note: "지난주 대비",
  },
]

export function StatCards() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon
        const Trend = card.up ? TrendingUp : TrendingDown
        return (
          <div
            key={card.label}
            className="rounded-xl border border-border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
          >
            <div className="flex items-start justify-between">
              <div className={cn("flex size-10 items-center justify-center rounded-lg", card.iconClass)}>
                <Icon className="size-5" />
              </div>
              <div
                className={cn(
                  "flex items-center gap-1 text-xs font-medium",
                  card.up ? "text-risk-low" : "text-muted-foreground",
                )}
              >
                <Trend className="size-3.5" />
                {card.trend}
              </div>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">{card.label}</p>
            <div className="mt-1 flex items-end gap-2">
              <span className={cn("text-3xl font-semibold tracking-tight tabular-nums", card.accent)}>
                {card.value.toLocaleString()}
              </span>
              <span className="pb-1 text-xs text-muted-foreground">명 · {card.note}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
