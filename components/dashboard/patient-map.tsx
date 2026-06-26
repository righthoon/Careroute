"use client"

import { useState } from "react"
import { MapPin, Layers, Maximize2, Plus, Minus } from "lucide-react"
import { mapMarkers, riskMeta, type RiskLevel } from "@/lib/dashboard-data"
import { cn } from "@/lib/utils"

const legend: { key: RiskLevel; label: string }[] = [
  { key: "high", label: "고위험" },
  { key: "medium", label: "중위험" },
  { key: "low", label: "저위험" },
]

export function PatientMap() {
  const [active, setActive] = useState<string | null>(null)

  return (
    <section className="flex flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border p-5">
        <div className="flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <MapPin className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">환자 분포 및 방문 우선순위 지도</h2>
            <p className="text-xs text-muted-foreground">천안시 권역별 관리 대상자 위치 현황</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-4 sm:flex">
            {legend.map((item) => (
              <div key={item.key} className="flex items-center gap-1.5">
                <span className={cn("size-2.5 rounded-full ring-2 ring-card", riskMeta[item.key].dot)} />
                <span className="text-xs text-muted-foreground">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="relative min-h-[420px] flex-1 overflow-hidden rounded-b-xl">
        {/* Map base — placeholder for Kakao Map API integration */}
        <img
          src="/map-base.png"
          alt="천안시 지역 지도 배경"
          className="absolute inset-0 size-full object-cover opacity-90"
        />
        <div className="absolute inset-0 bg-primary/5" />

        {/* Markers */}
        {mapMarkers.map((m) => {
          const meta = riskMeta[m.risk]
          const isActive = active === m.id
          return (
            <button
              key={m.id}
              onMouseEnter={() => setActive(m.id)}
              onMouseLeave={() => setActive(null)}
              onFocus={() => setActive(m.id)}
              onBlur={() => setActive(null)}
              className="group absolute -translate-x-1/2 -translate-y-full focus:outline-none"
              style={{ top: `${m.top}%`, left: `${m.left}%` }}
              aria-label={`${m.name} · ${meta.label}`}
            >
              <span className="relative flex flex-col items-center">
                {m.risk === "high" && (
                  <span
                    className={cn("absolute -top-1 size-7 animate-ping rounded-full opacity-40", meta.dot)}
                  />
                )}
                <MapPin
                  className={cn(
                    "relative size-7 drop-shadow-md transition-transform group-hover:scale-110",
                    meta.text,
                  )}
                  fill="currentColor"
                  strokeWidth={1.5}
                  stroke="white"
                />
                {isActive && (
                  <span className="absolute -top-9 z-10 whitespace-nowrap rounded-md bg-foreground px-2 py-1 text-[11px] font-medium text-background shadow-lg">
                    {m.name} · {meta.label}
                  </span>
                )}
              </span>
            </button>
          )
        })}

        {/* Map controls */}
        <div className="absolute right-4 top-4 flex flex-col gap-2">
          <div className="flex flex-col overflow-hidden rounded-lg border border-border bg-card shadow-sm">
            <button className="flex size-8 items-center justify-center text-muted-foreground transition-colors hover:bg-muted" aria-label="확대">
              <Plus className="size-4" />
            </button>
            <div className="h-px bg-border" />
            <button className="flex size-8 items-center justify-center text-muted-foreground transition-colors hover:bg-muted" aria-label="축소">
              <Minus className="size-4" />
            </button>
          </div>
          <button className="flex size-8 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground shadow-sm transition-colors hover:bg-muted" aria-label="레이어">
            <Layers className="size-4" />
          </button>
          <button className="flex size-8 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground shadow-sm transition-colors hover:bg-muted" aria-label="전체화면">
            <Maximize2 className="size-4" />
          </button>
        </div>

        {/* Integration note */}
        <div className="absolute bottom-4 left-4 rounded-lg border border-border bg-card/90 px-3 py-2 backdrop-blur-sm">
          <p className="text-[11px] font-medium text-foreground">Kakao Map API 연동 영역</p>
          <p className="text-[10px] text-muted-foreground">실시간 위치 데이터 연동 예정</p>
        </div>

        {/* Mobile legend */}
        <div className="absolute bottom-4 right-4 flex items-center gap-3 rounded-lg border border-border bg-card/90 px-3 py-2 backdrop-blur-sm sm:hidden">
          {legend.map((item) => (
            <div key={item.key} className="flex items-center gap-1.5">
              <span className={cn("size-2.5 rounded-full", riskMeta[item.key].dot)} />
              <span className="text-[11px] text-muted-foreground">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
