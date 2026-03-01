export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export type ChallengeStatus = 'active' | 'archived';
export type CollaboratorRole = 'owner' | 'collaborator';
export type SessionStatus = 'ideate' | 'build' | 'approved_for_analysis' | 'analysis_in_progress' | 'analysis_complete';
export type IdeaStatus = 'draft' | 'submitted';
export type AnalysisType = 'pros_cons' | 'feasibility' | 'impact' | 'summary';

export interface Challenge {
  id: number;
  title: string;
  description: string;
  status: ChallengeStatus;
  created_by: number;
  created_at: string;
  idea_count: number;
  session_status: SessionStatus | null;
}

export interface Idea {
  id: number;
  challenge_id: number;
  content: string;
  created_by: number;
  creator_name: string | null;
  status: IdeaStatus;
  tone_flag: boolean;
  suggested_alternative: string | null;
  created_at: string;
}

export interface SessionApproval {
  user_id: number;
  user_name: string;
  approved_at: string;
}

export interface GreenlightSession {
  id: number;
  challenge_id: number;
  status: SessionStatus;
  approved_at: string | null;
  created_at: string;
  approvals: SessionApproval[];
  total_collaborators: number;
  all_approved: boolean;
}

export interface IdeaDraft {
  id: number;
  idea_id: number;
  user_id: number;
  notes: string;
  want_pros_cons: boolean;
  want_feasibility: boolean;
  want_impact: boolean;
  updated_at: string;
}

export interface IdeaDraftUpdate {
  notes?: string;
  want_pros_cons?: boolean;
  want_feasibility?: boolean;
  want_impact?: boolean;
}

export interface Analysis {
  id: number;
  idea_id: number | null;
  challenge_id: number | null;
  analysis_type: AnalysisType;
  content: string;
  created_at: string;
}

export interface CreativityCheckResult {
  is_convergent: boolean;
  reason: string;
  suggested_alternative: string;
}

export interface Comment {
  id: number;
  idea_id: number;
  content: string;
  created_by: number;
  creator_name: string | null;
  tone_flag: boolean;
  suggested_alternative: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export type GroupRole = 'owner' | 'member';

export interface TeamMember {
  user_id: number;
  user_name: string;
  email: string;
  role: GroupRole;
}

export interface Team {
  id: number;
  name: string;
  members: TeamMember[];
}
