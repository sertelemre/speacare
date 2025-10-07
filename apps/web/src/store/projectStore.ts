import { create } from 'zustand';

interface Project {
  id: number;
  name: string;
  description: string;
  details: string;
  created_by: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  asset_count?: number;
}

interface ProjectAsset {
  id: number;
  project: number;
  name: string;
  asset_type: string;
  description: string;
  summary: string;
  file?: string;
  file_url?: string;
  url: string;
  mime_type: string;
  file_size?: number;
  created_by: string;
  created_at: string;
}

interface ProjectStore {
  selectedProject: Project | null;
  selectedAsset: ProjectAsset | null;
  setSelectedProject: (project: Project | null) => void;
  setSelectedAsset: (asset: ProjectAsset | null) => void;
  clearSelection: () => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  selectedProject: null,
  selectedAsset: null,
  setSelectedProject: (project) => set({ selectedProject: project, selectedAsset: null }),
  setSelectedAsset: (asset) => set({ selectedAsset: asset }),
  clearSelection: () => set({ selectedProject: null, selectedAsset: null }),
}));

export type { Project, ProjectAsset };
