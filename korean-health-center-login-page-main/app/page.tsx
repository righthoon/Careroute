import Image from "next/image"
import { Route, Database, Brain, ListChecks } from "lucide-react"
import { LoginForm } from "@/components/login-form"

export default function LoginPage() {
  return (
    <main className="flex min-h-svh items-center justify-center bg-background p-4 md:p-8">
      <div className="grid w-full max-w-6xl overflow-hidden rounded-2xl border border-border bg-card shadow-xl lg:grid-cols-[minmax(0,420px)_1fr]">
        {/* Left: login panel */}
        <div className="flex flex-col justify-center gap-8 p-8 sm:p-12">
          <header className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                <Route className="size-6" aria-hidden="true" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold text-foreground">CareRoute</span>
                <span className="text-xs font-medium text-muted-foreground">
                  AI 기반 방문건강관리 의사결정 지원 시스템
                </span>
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <h1 className="text-2xl font-bold text-balance text-foreground">로그인</h1>
              <p className="text-sm leading-relaxed text-muted-foreground">
                방문건강관리사업 담당자 전용 시스템입니다.
              </p>
            </div>
          </header>

          <LoginForm />
        </div>

        {/* Right: healthcare illustration */}
        <aside className="relative hidden flex-col justify-between gap-6 overflow-hidden bg-primary p-10 text-primary-foreground lg:flex">
          <div className="relative z-10 flex flex-col gap-2">
            <h2 className="text-3xl font-bold leading-snug text-balance">AI와 함께하는 방문건강관리</h2>
            <p className="max-w-md text-sm leading-relaxed text-primary-foreground/80">
              실시간 건강 데이터를 기반으로 고위험군을 조기에 발견하고 방문간호사의 효율적인 건강관리를 지원합니다.
            </p>
          </div>

          <div className="relative z-10 flex flex-1 items-center justify-center py-4">
            <div className="overflow-hidden rounded-2xl bg-card shadow-lg ring-1 ring-primary-foreground/10">
              <Image
                src="/images/visiting-nurse.png"
                alt="태블릿을 든 방문간호사가 가정에서 어르신에게 건강관리 서비스를 제공하는 모습"
                width={680}
                height={520}
                className="h-auto w-full object-cover"
                priority
              />
            </div>
          </div>

          <ul className="relative z-10 flex flex-wrap gap-x-6 gap-y-3 text-sm">
            <li className="flex items-center gap-2">
              <Database className="size-5 shrink-0" aria-hidden="true" />
              실시간 건강 데이터 연계
            </li>
            <li className="flex items-center gap-2">
              <Brain className="size-5 shrink-0" aria-hidden="true" />
              AI 기반 심뇌혈관질환 위험 예측
            </li>
            <li className="flex items-center gap-2">
              <ListChecks className="size-5 shrink-0" aria-hidden="true" />
              방문 우선순위 의사결정 지원
            </li>
          </ul>
        </aside>
      </div>
    </main>
  )
}
