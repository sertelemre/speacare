import { create } from 'zustand';

interface ThreadState {
  activeThreadId: number | null;
  setActiveThreadId: (threadId: number) => void;
  clearActiveThread: () => void;
}

export const useThreadStore = create<ThreadState>((set) => ({
  activeThreadId: null,
  setActiveThreadId: (threadId) => set({ activeThreadId: threadId }),
  clearActiveThread: () => set({ activeThreadId: null }),
}));
