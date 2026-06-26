"use client"

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import { PieChart as PieIcon } from "lucide-react"
import { riskDistribution, riskMeta, summaryStats } from "@/lib/dashboard-data"
import { cn } from "@/lib/utils"

const COLORS: Record<string, string> = {
  high: "var(--risk-high)",
  medium: "var(--risk-medium)",
  low: "var(--risk-low)",
}

export function RiskChart() {
  return (
    <section className="flex flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="flex items-center gap-2.5 border-b border-border p-5">
        <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <PieIcon className="size-5" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">위험도 분포</h2>
          <p className="text-xs text-muted-foreground">전체 대상자 위험 등급 비율</p>
        </div>
      </div>

      <div className="flex flex-1 flex-col items-center gap-4 p-5 sm:flex-row sm:gap-6">
        <div className="relative size-40 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={riskDistribution}
                dataKey="value"
                nameKey="name"
                innerRadius={52}
                outerRadius={76}
                paddingAngle={2}
                strokeWidth={0}
                startAngle={90}
                endAngle={-270}
              >
                {riskDistribution.map((entry) => (
                  <Cell key={entry.key} fill={COLORS[entry.key]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-semibold tabular-nums text-foreground">
              {summaryStats.total.toLocaleString()}
            </span>
            <span className="text-[11px] text-muted-foreground">총 대상자</span>
          </div>
        </div>

        <ul className="flex w-full flex-1 flex-col gap-3">
          {riskDistribution.map((entry) => {
            const meta = riskMeta[entry.key]
            const pct = Math.round((entry.value / summaryStats.total) * 100)
            return (
              <li key={entry.key} className="flex items-center gap-3">
                <span className={cn("size-2.5 rounded-full", meta.dot)} />
                <span className="text-sm text-foreground">{entry.name}</span>
                <span className="ml-auto text-sm font-medium tabular-nums text-foreground">
                  {entry.value.toLocaleString()}명
                </span>
                <span className="w-9 text-right text-xs tabular-nums text-muted-foreground">{pct}%</span>
              </li>
            )
          })}
        </ul>
      </div>
    </section>
  )
}
