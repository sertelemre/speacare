import { create } from 'zustand';

interface ChannelControlState {
  isChannelActive: boolean;
  activeChannels: Set<number>;
  setChannelActive: (channelId: number, isActive: boolean) => void;
  isChannelActiveById: (channelId: number) => boolean;
}

export const useChannelControlStore = create<ChannelControlState>((set, get) => ({
  isChannelActive: true,
  activeChannels: new Set(),
  
  setChannelActive: (channelId: number, isActive: boolean) => {
    set((state) => {
      const newActiveChannels = new Set(state.activeChannels);
      if (isActive) {
        newActiveChannels.add(channelId);
      } else {
        newActiveChannels.delete(channelId);
      }
      return {
        activeChannels: newActiveChannels,
        isChannelActive: newActiveChannels.size > 0,
      };
    });
  },
  
  isChannelActiveById: (channelId: number) => {
    return get().activeChannels.has(channelId);
  },
}));
