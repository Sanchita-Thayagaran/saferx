export type RiskLevel = 'GREEN' | 'YELLOW' | 'RED';

export interface DatabaseMatch {
  source: string;
  matched: boolean;
  record_id?: string | null;
  summary?: string | null;
  alert_type?: string | null;
  url?: string | null;
  confidence: number;
}

export interface ExtractedMedicineInfo {
  drug_name?: string | null;
  active_ingredient?: string | null;
  manufacturer?: string | null;
  batch_number?: string | null;
  expiry_date?: string | null;
  dosage_form?: string | null;
  strength?: string | null;
  country_of_origin?: string | null;
  raw_input: string;
}

export interface AnomalyFlag {
  flag_type: string;
  description: string;
  severity: RiskLevel;
}

export interface RiskAssessment {
  level: RiskLevel;
  score: number;
  reasoning: string;
  flags: AnomalyFlag[];
  citations: string[];
}

export interface ActionGuidance {
  summary: string;
  steps: string[];
  contact_authority?: string | null;
  emergency: boolean;
}

export interface RegulatoryReport {
  report_id: string;
  generated_at: string;
  markdown: string;
  json_payload: Record<string, unknown>;
}

export interface VerificationResponse {
  request_id: string;
  session_id?: string | null;
  timestamp: string;
  extracted_info: ExtractedMedicineInfo;
  database_matches: DatabaseMatch[];
  risk_assessment: RiskAssessment;
  action_guidance: ActionGuidance;
  report?: RegulatoryReport | null;
  risk_level: RiskLevel;
  verified: boolean;
  processing_time_ms?: number | null;
  reasoning_trace: string[];
  disclaimer: string;
}

export interface RiskConfig {
  color: string;
  label: string;
  icon: string;
  glow: string;
  spring: { stiffness: number; damping: number };
}

export type RiskConfigMap = Record<RiskLevel, RiskConfig>;
