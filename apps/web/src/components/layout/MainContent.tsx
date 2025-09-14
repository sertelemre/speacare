"use client";

import React, { useEffect } from 'react';
import { useChannelSocket } from '@/hooks/useChannelSocket';
import { useMessageStore } from '@/store/messageStore';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { useThreadStore } from '@/store/threadStore';
import { Button } from '@/components/ui/button';
import { MessageSquareText } from 'lucide-react';

// Mock channel ID for now
const CHANNEL_ID = 1;

interface Message {
  id: number;
  author_bot: string | null;
  author_user: string | null;
  author_type: 'user' | 'bot' | 'system';
  content_md: string;
  stance: string | null;
  thread_id?: number | null;
}

const fetchMessages = async (channelId: number): Promise<Message[]> => {
    const { data } = await api.get(`/api/channels/${channelId}/messages/`);
    return data;
};

export function MainContent() {
  useChannelSocket(CHANNEL_ID);
  const { messages, setMessages } = useMessageStore();
  const { setActiveThreadId } = useThreadStore();

  const { data: initialMessages, isLoading } = useQuery<Message[]>({
    queryKey: ['messages', CHANNEL_ID],
    queryFn: () => fetchMessages(CHANNEL_ID),
    enabled: !!CHANNEL_ID,
  });

  useEffect(() => {
    if (initialMessages) {
      setMessages(initialMessages);
    }
  }, [initialMessages, setMessages]);

  const getStanceColor = (stance: string | null) => {
    switch (stance) {
      case 'pro': return 'bg-green-500 hover:bg-green-600';
      case 'con': return 'bg-red-500 hover:bg-red-600';
      case 'neutral': return 'bg-gray-500 hover:bg-gray-600';
      default: return 'hidden';
    }
  };

  return (
    <main className="flex-1 p-4 overflow-y-auto">
      <div className="space-y-4">
        {isLoading && <p>Loading messages...</p>}
        {messages.map((msg) => (
          <div key={msg.id} className="flex items-start gap-4">
            <div className={`h-10 w-10 flex-shrink-0 rounded-full ${msg.author_type === 'bot' ? 'bg-blue-300' : 'bg-gray-300'}`}></div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="font-semibold">{msg.author_bot || msg.author_user}</p>
                {msg.author_type === 'bot' && (
                  <Badge className={getStanceColor(msg.stance)}>{msg.stance}</Badge>
                )}
              </div>
              <p className="text-gray-700 dark:text-gray-300">
                {msg.content_md}
              </p>
              {msg.thread_id && (
                <Button variant="link" size="sm" className="p-0 h-auto mt-1 text-blue-500" onClick={() => setActiveThreadId(msg.thread_id!)}>
                  <MessageSquareText className="mr-1 h-4 w-4" />
                  View Thread
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
