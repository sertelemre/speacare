"use client";

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from "sonner";

interface Bot {
  id: number;
  name: string;
}

interface Channel {
  id: number;
  name: string;
}

interface InviteBotDialogProps {
  bot: Bot;
  children: React.ReactNode; // To use as a trigger
}

// Fetcher for channels
const fetchChannels = async (): Promise<Channel[]> => {
  const { data } = await api.get('/api/channels/');
  return data;
};

// Mutation function to invite the bot
const inviteBotToChannel = async ({ channelId, botId }: { channelId: number, botId: number }) => {
    return api.post(`/api/channels/${channelId}/invite-bot/`, { bot_id: botId });
};

export const InviteBotDialog: React.FC<InviteBotDialogProps> = ({ bot, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<string>("");

  const { data: channels, isLoading: isLoadingChannels } = useQuery<Channel[]>({
    queryKey: ['channels'],
    queryFn: fetchChannels,
    enabled: isOpen, // Only fetch when the dialog is open
  });

  const mutation = useMutation({
    mutationFn: inviteBotToChannel,
    onSuccess: () => {
      toast.success(`Bot "${bot.name}" has been invited successfully!`);
      setIsOpen(false);
      // We don't necessarily need to refetch anything here unless we show bots per channel
    },
    onError: (error) => {
      toast.error("Failed to invite bot. It might already be in the channel.");
      console.error("Invite error:", error);
    },
  });

  const handleInvite = () => {
    if (!selectedChannel) {
      toast.warning("Please select a channel.");
      return;
    }
    mutation.mutate({ channelId: parseInt(selectedChannel), botId: bot.id });
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite &ldquo;{bot.name}&rdquo; to a Channel</DialogTitle>
          <DialogDescription>Select a channel to add this bot to the conversation.</DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <Select onValueChange={setSelectedChannel} value={selectedChannel} disabled={isLoadingChannels}>
            <SelectTrigger>
              <SelectValue placeholder="Select a channel..." />
            </SelectTrigger>
            <SelectContent>
              {channels && channels.map((channel) => (
                <SelectItem key={channel.id} value={String(channel.id)}>
                  # {channel.name}
                </SelectItem>
              ))}
              {isLoadingChannels && <SelectItem value="loading" disabled>Loading channels...</SelectItem>}
            </SelectContent>
          </Select>
        </div>
        <div className="flex justify-end">
            <Button onClick={handleInvite} disabled={mutation.isPending}>
                {mutation.isPending ? 'Inviting...' : 'Invite Bot'}
            </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
