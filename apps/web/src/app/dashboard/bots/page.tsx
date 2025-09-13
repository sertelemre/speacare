"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MoreHorizontal, PlusCircle, Trash2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { BotForm } from '@/components/bots/BotForm';
import { InviteBotDialog } from '@/components/bots/InviteBotDialog';
import { MessageSquarePlus } from 'lucide-react';

interface Bot {
  id: number;
  name: string;
  title: string;
  llm_provider: string;
  llm_model: string;
}

const fetchBots = async (): Promise<Bot[]> => {
  const { data } = await api.get('/api/bots/');
  return data;
};

const deleteBot = async (botId: number): Promise<void> => {
    await api.delete(`/api/bots/${botId}/`);
};

const BotsPage = () => {
  const queryClient = useQueryClient();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null);

  const { data: bots, isLoading, error } = useQuery<Bot[]>({
    queryKey: ['bots'],
    queryFn: fetchBots,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      setIsAlertOpen(false);
    },
  });

  const handleCreateClick = () => {
    setSelectedBot(null);
    setIsFormOpen(true);
  };

  const handleEditClick = (bot: Bot) => {
    setSelectedBot(bot);
    setIsFormOpen(true);
  };

  const handleDeleteClick = (bot: Bot) => {
    setSelectedBot(bot);
    setIsAlertOpen(true);
  };

  const handleConfirmDelete = () => {
    if (selectedBot) {
      deleteMutation.mutate(selectedBot.id);
    }
  };

  const handleFormSuccess = () => {
    setIsFormOpen(false);
    queryClient.invalidateQueries({ queryKey: ['bots'] });
  };

  return (
    <>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">My Bots</h1>
          <Button onClick={handleCreateClick}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Create New Bot
          </Button>
        </div>

        {isLoading && <p className="text-gray-500">Loading your bots...</p>}
        {error && <p className="text-red-500">Failed to load bots. Please try again later.</p>}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bots && bots.map((bot) => (
            <Card key={bot.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{bot.name}</CardTitle>
                    <CardDescription>{bot.title}</CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleEditClick(bot)}>Edit</DropdownMenuItem>
                       <InviteBotDialog bot={bot}>
                        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                          <MessageSquarePlus className="mr-2 h-4 w-4" />
                          Invite to Channel
                        </DropdownMenuItem>
                      </InviteBotDialog>
                      <DropdownMenuItem onClick={() => handleDeleteClick(bot)} className="text-red-500 hover:text-red-600">
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex space-x-2">
                  <Badge variant="outline">{bot.llm_provider}</Badge>
                  <Badge variant="secondary">{bot.llm_model}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {!isLoading && !error && bots?.length === 0 && (
          <div className="text-center py-12 border-2 border-dashed rounded-lg">
              <h3 className="text-lg font-medium">No Bots Found</h3>
              <p className="text-sm text-gray-500 mt-1">You haven't created any bots yet.</p>
              <Button className="mt-4" onClick={handleCreateClick}>
                <PlusCircle className="mr-2 h-4 w-4" />
                Create Your First Bot
              </Button>
          </div>
        )}
      </div>

      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedBot ? 'Edit Bot' : 'Create a New Bot'}</DialogTitle>
            <DialogDescription>
              {selectedBot ? 'Update the details for your bot.' : 'Fill out the form to create a new AI assistant.'}
            </DialogDescription>
          </DialogHeader>
          <BotForm bot={selectedBot} onSuccess={handleFormSuccess} />
        </DialogContent>
      </Dialog>

      <AlertDialog open={isAlertOpen} onOpenChange={setIsAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the bot
              <span className="font-semibold"> {selectedBot?.name}</span>.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? 'Deleting...' : 'Continue'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default BotsPage;
