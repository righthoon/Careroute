export type RiskLevel = "high" | "medium" | "low"

export const riskMeta: Record<
  RiskLevel,
  { label: string; dot: string; badge: string; text: string }
> = {
  high: {
    label: "고위험",
    dot: "bg-risk-high",
    badge: "bg-risk-high/10 text-risk-high border-risk-high/20",
    text: "text-risk-high",
  },
  medium: {
    label: "중위험",
    dot: "bg-risk-medium",
    badge: "bg-risk-medium/15 text-risk-medium border-risk-medium/25",
    text: "text-risk-medium",
  },
  low: {
    label: "저위험",
    dot: "bg-risk-low",
    badge: "bg-risk-low/10 text-risk-low border-risk-low/20",
    text: "text-risk-low",
  },
}

export const summaryStats = {
  total: 1284,
  high: 86,
  medium: 312,
  low: 886,
}

export type AiAlert = {
  id: string
  name: string
  age: number
  region: string
  reason: string
  score: number
  detectedAt: string
}

export const aiAlerts: AiAlert[] = [
  {
    id: "P-20471",
    name: "김순자",
    age: 78,
    region: "불당동",
    reason: "혈당·복약 데이터 급변, 최근 3일 미응답",
    score: 92,
    detectedAt: "12분 전",
  },
  {
    id: "P-20388",
    name: "박영수",
    age: 81,
    region: "월곶동",
    reason: "활동량 급감 + 낙상 위험 지표 상승",
    score: 89,
    detectedAt: "37분 전",
  },
  {
    id: "P-20512",
    name: "이말순",
    age: 74,
    region: "배곧1동",
    reason: "수축기 혈압 패턴 이상 감지",
    score: 85,
    detectedAt: "1시간 전",
  },
]

export type PriorityPatient = {
  id: string
  name: string
  age: number
  region: string
  score: number
  risk: RiskLevel
  lastSync: string
}

export const priorityPatients: PriorityPatient[] = [
  { id: "P-20471", name: "김순자", age: 78, region: "불당동", score: 92, risk: "high", lastSync: "12분 전" },
  { id: "P-20388", name: "박영수", age: 81, region: "월곶동", score: 89, risk: "high", lastSync: "37분 전" },
  { id: "P-20512", name: "이말순", age: 74, region: "배곧1동", score: 85, risk: "high", lastSync: "1시간 전" },
  { id: "P-20233", name: "정복희", age: 69, region: "신천동", score: 73, risk: "medium", lastSync: "2시간 전" },
  { id: "P-20620", name: "최광호", age: 72, region: "대야동", score: 68, risk: "medium", lastSync: "3시간 전" },
  { id: "P-20105", name: "한정자", age: 66, region: "은행동", score: 61, risk: "medium", lastSync: "4시간 전" },
]

export type Marker = {
  id: string
  risk: RiskLevel
  top: number
  left: number
  name: string
}

export const mapMarkers: Marker[] = [
  { id: "m1", risk: "high", top: 28, left: 22, name: "김순자" },
  { id: "m2", risk: "high", top: 54, left: 38, name: "박영수" },
  { id: "m3", risk: "high", top: 40, left: 68, name: "이말순" },
  { id: "m4", risk: "medium", top: 22, left: 55, name: "정복희" },
  { id: "m5", risk: "medium", top: 66, left: 60, name: "최광호" },
  { id: "m6", risk: "medium", top: 72, left: 28, name: "한정자" },
  { id: "m7", risk: "medium", top: 35, left: 45, name: "윤기철" },
  { id: "m8", risk: "low", top: 48, left: 18, name: "강미영" },
  { id: "m9", risk: "low", top: 60, left: 78, name: "조태식" },
  { id: "m10", risk: "low", top: 30, left: 82, name: "임순례" },
  { id: "m11", risk: "low", top: 78, left: 48, name: "서동수" },
  { id: "m12", risk: "low", top: 18, left: 38, name: "노경자" },
]

export const riskDistribution = [
  { name: "고위험", value: summaryStats.high, key: "high" as RiskLevel },
  { name: "중위험", value: summaryStats.medium, key: "medium" as RiskLevel },
  { name: "저위험", value: summaryStats.low, key: "low" as RiskLevel },
]

export type SyncRecord = {
  source: string
  description: string
  records: number
  status: "완료" | "동기화 중" | "지연"
  time: string
}

export const syncRecords: SyncRecord[] = [
  { source: "국민건강보험공단 API", description: "만성질환 코호트", records: 1284, status: "완료", time: "오늘 08:15" },
  { source: "웨어러블 디바이스", description: "활동량·심박 스트림", records: 642, status: "동기화 중", time: "실시간" },
  { source: "보건소 EMR", description: "방문 기록 업데이트", records: 318, status: "완료", time: "오늘 07:40" },
  { source: "AI 위험 분석 엔진", description: "위험 점수 재계산", records: 1284, status: "완료", time: "오늘 09:02" },
  { source: "복약 알림 시스템", description: "복약 순응도 로그", records: 207, status: "지연", time: "어제 23:50" },
]
