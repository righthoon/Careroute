"use client"

import { Bell, Search, ChevronDown, Menu, HeartPulse } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Topbar() {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-border bg-card/80 px-4 backdrop-blur-sm md:px-6">
      <div className="flex items-center gap-2 lg:hidden">
        <Button variant="ghost" size="icon" aria-label="메뉴 열기">
          <Menu className="size-5" />
        </Button>
        <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <HeartPulse className="size-4" />
        </div>
        <span className="text-sm font-semibold">CareRoute</span>
      </div>

      <div className="relative hidden max-w-md flex-1 md:block">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="search"
          placeholder="환자명, 지역, 환자번호 검색"
          className="h-9 w-full rounded-lg border border-border bg-background pl-9 pr-3 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/20"
          aria-label="검색"
        />
      </div>

      <div className="ml-auto flex items-center gap-2 md:gap-3">
        <Button variant="ghost" size="icon" className="relative" aria-label="알림">
          <Bell className="size-5" />
          <span className="absolute right-1.5 top-1.5 flex size-2">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-risk-high opacity-75" />
            <span className="relative inline-flex size-2 rounded-full bg-risk-high" />
          </span>
        </Button>

        <div className="h-6 w-px bg-border" />

        <button className="flex items-center gap-2.5 rounded-lg px-1.5 py-1 transition-colors hover:bg-muted">
          <span className="flex size-8 items-center justify-center rounded-full bg-accent text-sm font-semibold text-accent-foreground">
            이
          </span>
          <span className="hidden text-left leading-tight sm:block">
            <span className="block text-sm font-medium text-foreground">이지은 간호사</span>
            <span className="block text-[11px] text-muted-foreground">방문간호 2팀 팀장</span>
          </span>
          <ChevronDown className="hidden size-4 text-muted-foreground sm:block" />
        </button>
      </div>
    </header>
  )
}
