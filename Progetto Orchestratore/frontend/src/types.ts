export type JobItem = {
  title: string
  company?: string | null
  city?: string | null
  url?: string | null
  source?: string | null
}

export type ExtractResponse = {
  job_title: string
  city: string
  count: number
  report_path?: string | null
  items: JobItem[]
}