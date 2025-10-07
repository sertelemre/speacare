import { create } from 'zustand';

interface Bot {
  id: number;
  name: string;
  title: string;
  character: string;
  job_description: string;
  llm_provider: string;
  llm_model: string;
  temperature?: number;
  color?: string;
}

interface BotStore {
  selectedBot: Bot | null;
  isBotViewActive: boolean;
  setSelectedBot: (bot: Bot | null) => void;
  setBotViewActive: (active: boolean) => void;
  clearSelection: () => void;
}

export const useBotStore = create<BotStore>((set) => ({
  selectedBot: null,
  isBotViewActive: false,
  setSelectedBot: (bot) => set({ selectedBot: bot }),
  setBotViewActive: (active) => set({ isBotViewActive: active }),
  clearSelection: () => set({ selectedBot: null, isBotViewActive: false }),
}));

export type { Bot };
