import { create } from 'zustand';

// Assuming the Message type is similar to what the backend serializer provides
// interface Author {
//     username?: string;
//     name?: string;
// }

interface BotAuthor {
  name: string;
  color: string;
}

interface Message {
  id: number;
  author_user: string | null; // username
  author_bot: string | BotAuthor | null; // bot name or bot object with name and color
  author_type: 'user' | 'bot' | 'system';
  content_md: string;
  stance: 'pro' | 'con' | 'neutral' | null;
  thread_id?: number | null;
  created_at: string;
}

interface MessageState {
  messages: Message[];
  thinkingBots: Set<string>;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  addThinkingBot: (botName: string) => void;
  removeThinkingBot: (botName: string) => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  thinkingBots: new Set(),
  addMessage: (message) => {
    console.log('MessageStore: Adding message:', message);
    set((state) => {
      // Check if message already exists (prevent duplicates)
      const messageExists = state.messages.some(msg => msg.id === message.id);
      if (messageExists) {
        console.log('MessageStore: Message already exists, skipping:', message.id);
        return state;
      }
      
      const newMessages = [...state.messages, message];
      console.log('MessageStore: New messages array length:', newMessages.length);
      return { messages: newMessages };
    });
  },
  setMessages: (messages) => set({ messages }),
  addThinkingBot: (botName) => set((state) => ({ 
    thinkingBots: new Set([...state.thinkingBots, botName]) 
  })),
  removeThinkingBot: (botName) => set((state) => {
    const newSet = new Set(state.thinkingBots);
    newSet.delete(botName);
    return { thinkingBots: newSet };
  }),
}));
