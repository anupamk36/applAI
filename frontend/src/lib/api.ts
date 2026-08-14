import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface Fact {
  id: string
  kind: string
  payload: Record<string, string>
  confirmed_at: string | null
  source: string
  version: number
}

export interface Resume {
  id: string
  kind: string
  original_filename: string
  parsed_at: string | null
  is_base: boolean
}

export interface JobPreferences {
  target_titles: string[]
  locations: string[]
  target_countries: string[]
  ctc_min: number | null
  ctc_max: number | null
  industries: string[]
  company_size_bands: string[]
  blocklist_companies: string[]
}

export interface Settings {
  threshold: number
  daily_cap: number
  auto_apply_enabled: boolean
  calibration_complete: boolean
  job_preferences: JobPreferences
}

export interface JobList {
  items: Job[]
  total: number
  limit: number
  offset: number
}

export interface AnswerBankEntry {
  semantic_key: string
  label: string
  value: string
  is_sensitive: boolean
  policy: string
  version: number
}

export interface MatchedJob {
  job_id: string
  company_name: string
  title: string
  score: number
  limiting_factors: string[]
  computed_at: string
}

export interface OpportunityReport {
  scanned: number
  passed_hard_filters: number
  excluded_by_reason: Record<string, number>
  met_quality_bar: number
  below_threshold: number
  threshold: number
  matched: MatchedJob[]
  near_misses: MatchedJob[]
}

export interface Job {
  id: string
  company_id: string
  company_name: string
  title: string
  seniority_band: string | null
  skills: string[]
  exp_min: number | null
  exp_max: number | null
  ctc_min: number | null
  ctc_max: number | null
  locations: string[]
  remote_policy: string | null
  ats: string | null
  apply_url: string
  first_seen_at: string
  last_seen_at: string
}
