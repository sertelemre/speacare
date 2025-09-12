import { create } from 'zustand';

// Assuming the Message type is similar to what the backend serializer provides
interface Author {
    username?: string;
    name?: string;
}

interface Message {
  id: number;
  author_user: string | null; // username
  author_bot: string | null; // bot name
  author_type: 'user' | 'bot' | 'system';
  content_md: string;
  stance: 'pro' | 'con' | 'neutral' | null;
  created_at: string;
}

interface MessageState {
  messages: Message[];
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
}));
