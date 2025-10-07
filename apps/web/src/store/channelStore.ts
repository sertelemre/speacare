import { create } from 'zustand';

interface Channel {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  waiting_for_user?: string | null;
  projects?: Array<{ id: number; name: string }>;
}

interface ChannelState {
  selectedChannel: Channel | null;
  setSelectedChannel: (channel: Channel | null) => void;
}

export const useChannelStore = create<ChannelState>((set) => ({
  selectedChannel: null,
  setSelectedChannel: (channel) => set({ selectedChannel: channel }),
}));
