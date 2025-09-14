"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useThreadStore } from '@/store/threadStore';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { X, Send } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

// This should be the same as in MainContent.tsx
interface Message {
  id: number;
  author_bot: string | null;
  author_user: string | null;
  author_type: 'user' | 'bot' | 'system';
  content_md: string;
  stance: string | null;
  thread_id?: number | null;
}

// Fetcher for a specific thread's messages
const fetchThreadMessages = async (channelId: number, threadId: number): Promise<Message[]> => {
  const { data } = await api.get(`/api/channels/${channelId}/messages/?thread_id=${threadId}`);
  return data;
};

// Mutation for posting a new reply
const postReply = async ({ channelId, threadId, content }: { channelId: number, threadId: number, content: string }) => {
    const { data } = await api.post(`/api/channels/${channelId}/messages/`, {
        content_md: content,
        thread_id: threadId,
    });
    return data;
}

// TODO: This should come from a dynamic context
const CHANNEL_ID = 1;

export function ThreadView() {
  const { activeThreadId, clearActiveThread } = useThreadStore();
  const [reply, setReply] = useState('');
  const queryClient = useQueryClient();

  const { data: messages, isLoading, error } = useQuery<Message[]>({
    queryKey: ['messages', 'thread', activeThreadId],
    queryFn: () => fetchThreadMessages(CHANNEL_ID, activeThreadId!),
    enabled: !!activeThreadId, // Only run the query if there's an active thread
  });

  const mutation = useMutation({
      mutationFn: postReply,
      onSuccess: () => {
          // Invalidate both the main message query and the thread-specific one
          queryClient.invalidateQueries({ queryKey: ['messages', 'thread', activeThreadId] });
          queryClient.invalidateQueries({ queryKey: ['messages', CHANNEL_ID] });
          setReply('');
      },
      onError: () => {
        // TODO: Add user-facing error handling (e.g., toast)
        console.error("Failed to post reply");
      }
  });

  const handleReplySubmit = (e: React.FormEvent) => {
      e.preventDefault();
      if (reply.trim() && activeThreadId) {
          mutation.mutate({ channelId: CHANNEL_ID, threadId: activeThreadId, content: reply });
      }
  };

  const getStanceColor = (stance: string | null) => {
    switch (stance) {
      case 'pro': return 'bg-green-500 hover:bg-green-600';
      case 'con': return 'bg-red-500 hover:bg-red-600';
      case 'neutral': return 'bg-gray-500 hover:bg-gray-600';
      default: return 'hidden';
    }
  };

  if (!activeThreadId) return null;

  return (
    <div className="bg-white dark:bg-gray-900 h-full flex flex-col">
      <header className="p-4 border-b dark:border-gray-800 flex justify-between items-center">
        <div>
            <h2 className="font-semibold">Thread</h2>
            {/* TODO: Fetch and display thread topic */}
            <p className="text-xs text-gray-500">Replies to a message</p>
        </div>
        <Button variant="ghost" size="icon" onClick={clearActiveThread}>
          <X className="h-5 w-5" />
        </Button>
      </header>

      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {isLoading && <p>Loading thread...</p>}
        {error && <p>Error loading thread.</p>}
        {messages?.map((msg) => (
            <div key={msg.id} className="flex items-start gap-3">
                <div className={`h-8 w-8 flex-shrink-0 rounded-full ${msg.author_type === 'bot' ? 'bg-blue-300' : 'bg-gray-300'}`}></div>
                <div className="flex-1">
                    <div className="flex items-center gap-2">
                        <p className="font-semibold text-sm">{msg.author_bot || msg.author_user}</p>
                        {msg.author_type === 'bot' && (
                        <Badge className={`${getStanceColor(msg.stance)} text-xs`} style={{padding: '2px 4px', height: 'auto'}}>{msg.stance}</Badge>
                        )}
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                        {msg.content_md}
                    </p>
                </div>
            </div>
        ))}
      </div>

      <footer className="p-4 border-t dark:border-gray-800">
        <form onSubmit={handleReplySubmit} className="flex items-center gap-2">
          <Input
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            placeholder="Reply..."
            className="flex-1"
            disabled={mutation.isPending}
          />
          <Button type="submit" size="icon" disabled={!reply.trim() || mutation.isPending}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </footer>
    </div>
  );
}
