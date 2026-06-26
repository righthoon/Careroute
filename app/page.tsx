import { Sidebar } from "@/components/dashboard/sidebar"
import { Topbar } from "@/components/dashboard/topbar"
import { StatCards } from "@/components/dashboard/stat-cards"
import { AiAlertPanel } from "@/components/dashboard/ai-alert-panel"
import { VisitPriority } from "@/components/dashboard/visit-priority"
import { PatientMap } from "@/components/dashboard/patient-map"
import { RiskChart } from "@/components/dashboard/risk-chart"
import { SyncPanel } from "@/components/dashboard/sync-panel"

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 space-y-6 p-4 md:p-6">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-foreground">
                방문건강관리 대시보드
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                2026년 6월 23일 화요일 · 인구 단위 모니터링 및 방문 계획 현황
              </p>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground">
              <span className="size-1.5 rounded-full bg-risk-low" />
              실시간 연동 활성
            </span>
          </div>

          <StatCards />

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <PatientMap />
            </div>
            <AiAlertPanel />
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <VisitPriority />
            </div>
            <RiskChart />
          </div>

          <SyncPanel />
        </main>
      </div>
    </div>
  )
}
