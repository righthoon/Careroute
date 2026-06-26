"use client"

import { useState } from "react"
import {
  LayoutDashboard,
  Users,
  Brain,
  CalendarClock,
  FileBarChart,
  Settings,
  HeartPulse,
} from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { label: "대시보드", icon: LayoutDashboard, key: "dashboard" },
  { label: "환자 관리", icon: Users, key: "patients" },
  { label: "AI 위험 분석", icon: Brain, key: "ai" },
  { label: "방문 계획", icon: CalendarClock, key: "visits" },
  { label: "리포트", icon: FileBarChart, key: "reports" },
  { label: "설정", icon: Settings, key: "settings" },
]

export function Sidebar() {
  const [active, setActive] = useState("dashboard")

  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground lg:flex">
      <div className="flex h-16 items-center gap-2.5 px-6">
        <div className="flex size-9 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
          <HeartPulse className="size-5" />
        </div>
        <div className="leading-tight">
          <p className="text-base font-semibold tracking-tight text-white">CareRoute</p>
          <p className="text-[11px] text-sidebar-foreground/60">방문건강관리 플랫폼</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
        <p className="px-3 pb-2 text-[11px] font-medium uppercase tracking-wider text-sidebar-foreground/40">
          메뉴
        </p>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = active === item.key
          return (
            <button
              key={item.key}
              onClick={() => setActive(item.key)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground"
                  : "text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-white",
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className="size-[18px]" />
              {item.label}
            </button>
          )
        })}
      </nav>

      <div className="m-3 rounded-xl bg-sidebar-accent p-4">
        <p className="text-xs font-medium text-white">천안시 보건소</p>
        <p className="mt-1 text-[11px] leading-relaxed text-sidebar-foreground/60">
          방문간호 4팀 · 담당자 12명
        </p>
        <div className="mt-3 flex items-center gap-2">
          <span className="inline-block size-1.5 rounded-full bg-risk-low" />
          <span className="text-[11px] text-sidebar-foreground/70">시스템 정상 운영 중</span>
        </div>
      </div>
    </aside>
  )
}
