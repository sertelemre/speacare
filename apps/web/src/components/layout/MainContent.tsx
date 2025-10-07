"use client";

import React, { useEffect, useRef } from 'react';
import { useChannelSocket } from '@/hooks/useChannelSocket';
import { useMessageStore } from '@/store/messageStore';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { useThreadStore } from '@/store/threadStore';
import { useChannelStore } from '@/store/channelStore';
import { useProjectStore } from '@/store/projectStore';
import { useBotStore } from '@/store/botStore';
import { Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MessageSquareText, Send, Pause, Play, Bot, Users, Trash2 } from 'lucide-react';
import { ProjectDetail } from '@/components/projects/ProjectDetail';
import { AssetDetail } from '@/components/projects/AssetDetail';
import { BotList } from '@/components/bots/BotList';
import { BotDetail } from '@/components/bots/BotDetail';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

interface BotAuthor {
  name: string;
  color: string;
}

interface Message {
  id: number;
  author_bot: string | BotAuthor | null;
  author_user: string | null;
  author_type: 'user' | 'bot' | 'system';
  content_md: string;
  stance: 'pro' | 'con' | 'neutral' | null;
  thread_id?: number | null;
  created_at: string;
}

interface ChannelBot {
  id: number;
  bot: {
    id: number;
    name: string;
    character: string;
    job_description: string;
    llm_provider: string;
    llm_model: string;
    color?: string;
  };
  is_active: boolean;
  join_policy: 'always' | 'on_mention' | 'topic_based';
}

const fetchMessages = async (channelId: number): Promise<Message[]> => {
    const { data } = await api.get(`/api/channels/${channelId}/messages/`);
    return data;
};

const sendMessage = async (channelId: number, content: string): Promise<Message> => {
    const { data } = await api.post(`/api/channels/${channelId}/messages/`, {
        content_md: content,
        author_type: 'user'
    });
    return data;
};

const fetchChannelBots = async (channelId: number): Promise<ChannelBot[]> => {
    const { data } = await api.get(`/api/channels/${channelId}/bots/`);
    return data;
};

const clearChannelMessages = async (channelId: number): Promise<{deleted_count: number}> => {
    const { data } = await api.post(`/api/channels/${channelId}/clear-messages/`);
    return data;
};

export function MainContent() {
  const { selectedChannel, setSelectedChannel } = useChannelStore();
  const { selectedProject } = useProjectStore();
  const { selectedBot, isBotViewActive } = useBotStore();
  const { messages, setMessages, addMessage, thinkingBots } = useMessageStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const { setActiveThreadId } = useThreadStore();
  const [newMessage, setNewMessage] = useState('');
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [hoveredBot, setHoveredBot] = useState<string | null>(null);
  const queryClient = useQueryClient();

  useChannelSocket(selectedChannel?.id ?? null);

  const { data: initialMessages, isLoading } = useQuery<Message[]>({
    queryKey: ['messages', selectedChannel?.id],
    queryFn: () => fetchMessages(selectedChannel!.id),
    enabled: !!selectedChannel?.id,
  });

  const { data: channelBots } = useQuery<ChannelBot[]>({
    queryKey: ['channel-bots', selectedChannel?.id],
    queryFn: () => fetchChannelBots(selectedChannel!.id),
    enabled: !!selectedChannel?.id,
  });

  const sendMessageMutation = useMutation({
    mutationFn: ({ channelId, content }: { channelId: number; content: string }) => 
      sendMessage(channelId, content),
    onSuccess: (newMsg) => {
      addMessage(newMsg);
      setNewMessage('');
      queryClient.invalidateQueries({ queryKey: ['messages', selectedChannel?.id] });
    },
    onError: (error) => {
      toast.error('Failed to send message');
      console.error('Error sending message:', error);
    },
  });

  const clearMessagesMutation = useMutation({
    mutationFn: (channelId: number) => clearChannelMessages(channelId),
    onSuccess: (result) => {
      setMessages([]);
      queryClient.invalidateQueries({ queryKey: ['messages', selectedChannel?.id] });
      toast.success(`Chat history cleared. ${result.deleted_count} messages deleted.`);
    },
    onError: (error) => {
      toast.error('Failed to clear chat history');
      console.error('Error clearing messages:', error);
    },
  });

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMessage.trim() && selectedChannel) {
      sendMessageMutation.mutate({
        channelId: selectedChannel.id,
        content: newMessage.trim(),
      });
    }
  };

  const handleToggleChannel = () => {
    if (selectedChannel) {
      const isActive = selectedChannel.is_active;
      const endpoint = isActive ? 'stop' : 'start';
      
      api.post(`/api/channels/${selectedChannel.id}/${endpoint}-bots/`)
        .then(() => {
          // Update the channel data in the store
          setSelectedChannel({
            ...selectedChannel,
            is_active: !isActive
          });
          
          // Refresh channels list
          queryClient.invalidateQueries({ queryKey: ['channels'] });
          
          toast.success(isActive ? 'Bot conversations stopped' : 'Bot conversations started');
        })
        .catch((error) => {
          console.error('Failed to control bot conversations:', error);
          toast.error('Failed to control bot conversations');
        });
    }
  };

  const handleClearMessages = () => {
    if (selectedChannel) {
      if (confirm('Are you sure you want to clear all messages in this channel? This action cannot be undone.')) {
        clearMessagesMutation.mutate(selectedChannel.id);
      }
    }
  };

  // Mention'ları mavi renkte göstermek için fonksiyon
  const renderMessageContent = (content: string) => {
    // @mention pattern'ini bul ve mavi renkte göster
    const mentionRegex = /@(\w+)/g;
    const parts = content.split(mentionRegex);
    
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        // Bu bir mention (tek index'ler mention'lar)
        return (
          <span key={index} className="text-blue-500 font-medium cursor-pointer hover:text-blue-600 hover:underline">
            @{part}
          </span>
        );
      }
      return part;
    });
  };

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'instant' });
  };

  // Check if user is near the bottom of the chat
  const isNearBottom = () => {
    const messagesContainer = messagesContainerRef.current;
    if (!messagesContainer) return true;
    
    const { scrollTop, scrollHeight, clientHeight } = messagesContainer;
    const threshold = 100; // pixels from bottom
    return scrollHeight - scrollTop - clientHeight < threshold;
  };

  // Handle scroll events to detect if user is reading older messages
  const handleScroll = () => {
    setShouldAutoScroll(isNearBottom());
  };

  // Scroll to bottom when messages change, but only if user is near bottom
  useEffect(() => {
    if (shouldAutoScroll) {
      // Use setTimeout to ensure DOM is updated
      setTimeout(() => {
        scrollToBottom();
      }, 0);
    }
  }, [messages, shouldAutoScroll]);

  useEffect(() => {
    if (initialMessages) {
      setMessages(initialMessages);
      setShouldAutoScroll(true); // Reset auto-scroll when loading new messages
    }
  }, [initialMessages, setMessages]);

  // Add scroll event listener
  useEffect(() => {
    const messagesContainer = messagesContainerRef.current;
    if (messagesContainer) {
      messagesContainer.addEventListener('scroll', handleScroll);
      return () => {
        messagesContainer.removeEventListener('scroll', handleScroll);
      };
    }
  }, []);

  const getStanceColor = (stance: string | null) => {
    switch (stance) {
      case 'pro': return 'bg-green-500 hover:bg-green-600';
      case 'con': return 'bg-red-500 hover:bg-red-600';
      case 'neutral': return 'bg-gray-500 hover:bg-gray-600';
      default: return 'hidden';
    }
  };

  // If a project is selected, show project view
  if (selectedProject) {
    // Force clear channel selection when project is selected
    if (selectedChannel) {
      setSelectedChannel(null);
    }
    
    return (
      <div className="flex-1 flex">
        <ProjectDetail />
        <AssetDetail />
      </div>
    );
  }

  // If bot view is active, show bot view
  if (isBotViewActive) {
    return (
      <div className="flex-1 flex">
        <BotList />
        <BotDetail />
      </div>
    );
  }

  if (!selectedChannel) {
    return (
      <main className="flex-1 p-4 overflow-y-auto min-h-0">
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-gray-500 mb-2">Welcome to SpeaCare</h2>
            <p className="text-gray-400">Select a channel from the sidebar to start chatting, or create a new project to get started.</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* Channel Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h1 className="text-2xl font-bold">#{selectedChannel.name}</h1>
            {selectedChannel.description && (
              <p className="text-gray-500 mt-1">{selectedChannel.description}</p>
            )}
            
            {/* Active Bots Avatars */}
            {channelBots && channelBots.length > 0 && (
              <div className="mt-3">
                <div className="flex items-center gap-2 mb-2">
                  <Bot className="h-4 w-4 text-blue-500" />
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Active Bots ({channelBots.filter(cb => cb.is_active).length}/{channelBots.length})
                  </span>
                </div>
                <div className="flex items-center gap-2 relative">
                  {channelBots
                    .filter(channelBot => channelBot.is_active)
                    .map((channelBot) => (
                      <div
                        key={channelBot.id}
                        className="relative"
                        onMouseEnter={() => setHoveredBot(channelBot.bot.name)}
                        onMouseLeave={() => setHoveredBot(null)}
                      >
                        <div 
                          className="h-8 w-8 rounded-full text-white flex items-center justify-center text-sm font-semibold hover:opacity-80 transition-opacity cursor-pointer"
                          style={{ backgroundColor: channelBot.bot.color || '#3B82F6' }}
                        >
                          {channelBot.bot.name.charAt(0).toUpperCase()}
                        </div>
                        
                        {/* Tooltip */}
                        {hoveredBot === channelBot.bot.name && (
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg z-50 whitespace-nowrap">
                            <div className="text-center">
                              <p className="font-semibold">{channelBot.bot.name}</p>
                              <p className="text-gray-300">{channelBot.bot.job_description}</p>
                              <p className="text-gray-400 mt-1">
                                {channelBot.join_policy === 'always' ? 'Always Active' :
                                 channelBot.join_policy === 'on_mention' ? 'Mention Only' :
                                 'Topic-based'}
                              </p>
                            </div>
                            {/* Arrow */}
                            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2 ml-4">
            <Button
              onClick={handleClearMessages}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
              disabled={clearMessagesMutation.isPending}
            >
              <Trash2 className="h-4 w-4" />
              Clear Chat
            </Button>
            
            <Button
              onClick={handleToggleChannel}
              variant={selectedChannel.is_active ? "destructive" : "default"}
              size="sm"
              className="flex items-center gap-2"
            >
              {selectedChannel.is_active ? (
                <>
                  <Pause className="h-4 w-4" />
                  Stop Bots
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Start Bots
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div ref={messagesContainerRef} className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-4">
          {isLoading && <p>Loading messages...</p>}
          {messages.map((msg) => {
            // Get bot color and name from message data or channel bots
            let botColor = null;
            let botName = null;
            
            if (msg.author_type === 'bot' && msg.author_bot) {
              if (typeof msg.author_bot === 'object' && 'color' in msg.author_bot) {
                // New format with color in message
                botColor = msg.author_bot.color || '#3B82F6';
                botName = msg.author_bot.name;
              } else {
                // Fallback: get color from channel bots
                const botNameStr = typeof msg.author_bot === 'string' ? msg.author_bot : msg.author_bot;
                botName = botNameStr;
                
                // Find bot color from channel bots
                const channelBot = channelBots?.find(cb => cb.bot.name === botNameStr);
                botColor = channelBot?.bot.color || '#3B82F6';
              }
            }
              
            return (
            <div key={msg.id} className="flex items-start gap-4 animate-in slide-in-from-bottom-2 duration-150">
              <div 
                className={`h-10 w-10 flex-shrink-0 rounded-full flex items-center justify-center text-white font-semibold ${
                  msg.author_type === 'bot' ? '' : 'bg-gray-300'
                }`}
                style={msg.author_type === 'bot' && botColor ? { backgroundColor: botColor } : {}}
              >
                {msg.author_type === 'bot' ? (botName?.charAt(0).toUpperCase() || 'B') : msg.author_user?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-semibold">{msg.author_type === 'bot' ? botName : msg.author_user}</p>
                  {msg.author_type === 'bot' && (
                    <Badge className={getStanceColor(msg.stance)}>{msg.stance}</Badge>
                  )}
                </div>
                <p className="text-gray-700 dark:text-gray-300">
                  {renderMessageContent(msg.content_md)}
                </p>
                {msg.thread_id && (
                  <Button variant="link" size="sm" className="p-0 h-auto mt-1 text-blue-500" onClick={() => setActiveThreadId(msg.thread_id!)}>
                    <MessageSquareText className="mr-1 h-4 w-4" />
                    View Thread
                  </Button>
                )}
              </div>
            </div>
            );
          })}
          {!isLoading && messages.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              <p>No messages yet. Start the conversation!</p>
            </div>
          )}
          {/* Auto-scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Bot Thinking Indicator */}
      {thinkingBots.size > 0 && (
        <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20">
          <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
            <Bot className="h-4 w-4 animate-pulse" />
            <span>
              {Array.from(thinkingBots).map((botName, index) => (
                <span key={botName}>
                  {botName} is thinking...
                  {index < thinkingBots.size - 1 && ', '}
                </span>
              ))}
            </span>
          </div>
        </div>
      )}

      {/* Waiting for User Indicator */}
      {selectedChannel?.waiting_for_user && (
        <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-yellow-50 dark:bg-yellow-900/20">
          <div className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
            <Clock className="h-4 w-4" />
            <span>
              Waiting for {selectedChannel.waiting_for_user} to respond...
            </span>
          </div>
        </div>
      )}

      {/* Message Input */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <Input
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1"
            disabled={sendMessageMutation.isPending}
          />
          <Button 
            type="submit" 
            disabled={!newMessage.trim() || sendMessageMutation.isPending}
            size="sm"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </main>
  );
}
