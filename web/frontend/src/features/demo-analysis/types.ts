import { z } from 'zod'

export const PeakDataSchema = z.object({
  frequency_hz: z.number(),
  amplitude_db: z.number(),
  type: z.string(),
})

export const SignalDataSchema = z.object({
  time_s: z.array(z.number()),
  raw: z.array(z.number()),
  filtered: z.array(z.number()),
  rms_trend: z.array(z.number()),
})

export const SpectrumDataSchema = z.object({
  frequencies_hz: z.array(z.number()),
  psd: z.array(z.number()),
  peaks: z.array(PeakDataSchema),
})

export const SummaryDataSchema = z.object({
  risk_level: z.string().nullable(),
  risk_label_ru: z.string().nullable(),
  dominant_peak_hz: z.number().nullable(),
  rms_total: z.number().nullable(),
  reynolds_number: z.number().nullable(),
  strouhal_number: z.number().nullable(),
})

export const AnalysisResponseSchema = z.object({
  analysis_id: z.string(),
  is_demo: z.boolean(),
  demo_title: z.string().nullable(),
  summary: SummaryDataSchema,
  signal: SignalDataSchema,
  spectrum: SpectrumDataSchema,
  warnings: z.array(z.string()),
})

export const DemoScenarioItemSchema = z.object({
  key: z.string(),
  title_ru: z.string(),
  description_ru: z.string(),
  expected_peak_hz: z.number().nullable(),
})

export const DemoScenariosResponseSchema = z.object({
  items: z.array(DemoScenarioItemSchema),
})

export type AnalysisResponse = z.infer<typeof AnalysisResponseSchema>
export type DemoScenarioItem = z.infer<typeof DemoScenarioItemSchema>
export type DemoScenariosResponse = z.infer<typeof DemoScenariosResponseSchema>
